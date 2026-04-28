from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router
from .schemas import HomeDataSchema, CourseDetailSchema
from core.responses import success_response, StandardResponse
from .models import Course, Category, Banner, UserProgress
from core.idempotency import idempotent

router = Router()

@router.get("/home", response={200: StandardResponse})
@idempotent(timeout=300)
def get_home_data(request):
    # Fetch categories
    categories_qs = Category.objects.all().order_by('order')
    categories = ["All"] + [cat.name for cat in categories_qs]

    # Fetch active banners
    banners_qs = Banner.objects.filter(is_active=True).order_by('order')
    banners = []
    for b in banners_qs:
        color_start = int(b.color_start, 16) if b.color_start.startswith('0x') else 0
        color_end = int(b.color_end, 16) if b.color_end.startswith('0x') else 0
        banners.append({
            "title": b.title,
            "subtitle": b.subtitle,
            "badge": b.badge,
            "image": b.image.url if b.image else "",
            "colors": [color_start, color_end]
        })

    # Fetch featured courses with select_related for N+1 optimization
    featured_qs = Course.objects.filter(is_published=True, is_featured=True).select_related('instructor', 'category')
    featured_courses = []
    for c in featured_qs:
        featured_courses.append({
            "id": str(c.id),
            "title": c.title,
            "instructor": c.instructor.name if c.instructor else "Unknown",
            "category": c.category.name if c.category else "Uncategorized",
            "image": c.thumbnail.url if c.thumbnail else "",
            "progress": None, # Could be calculated if user is logged in
            "rating": c.rating,
            "reviews": c.reviews_count,
            "price": float(c.price),
            "original_price": float(c.original_price),
            "badge": c.badge,
            "discount": c.discount
        })

    # Fetch continue learning (mock logic, ideally based on request.user)
    continue_learning = []
    if request.user.is_authenticated:
        # Example optimization for continue learning
        progress_qs = UserProgress.objects.filter(user=request.user).select_related(
            'lesson__section__course__instructor', 
            'lesson__section__course__category'
        ).order_by('-last_watched_at')[:5]
        
        # Deduplicate courses
        seen_courses = set()
        for p in progress_qs:
            c = p.lesson.section.course
            if c.id not in seen_courses:
                seen_courses.add(c.id)
                continue_learning.append({
                    "id": str(c.id),
                    "title": c.title,
                    "instructor": c.instructor.name if c.instructor else "Unknown",
                    "category": c.category.name if c.category else "Uncategorized",
                    "image": c.thumbnail.url if c.thumbnail else "",
                    "progress": 0.5, # Calculate real progress
                    "rating": c.rating,
                    "reviews": c.reviews_count,
                    "price": float(c.price),
                    "original_price": float(c.original_price),
                    "badge": c.badge,
                    "discount": c.discount
                })

    data = {
        "categories": categories,
        "banners": banners,
        "continue_learning": continue_learning,
        "featured_courses": featured_courses
    }
    return success_response(data=data)

@router.get("/courses/{course_id}", response={200: StandardResponse})
@idempotent(timeout=300)
def get_course_detail(request, course_id: str):
    # Fetch course with related data
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category').prefetch_related('sections__lessons'), 
        id=course_id
    )
    
    curriculum = []
    for section in course.sections.all():
        lessons = []
        for lesson in section.lessons.all():
            lessons.append({
                "id": str(lesson.id),
                "title": lesson.title,
                "duration": lesson.duration_str,
                "video_url": lesson.video_url,
                "is_preview": lesson.is_preview,
                "is_completed": False # Calculate from UserProgress if authenticated
            })
        curriculum.append({
            "id": str(section.id),
            "title": section.title,
            "lessons": lessons
        })

    data = {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "instructor": course.instructor.name if course.instructor else "Unknown",
        "instructor_avatar": "", # Update if user model gets avatar
        "instructor_role": "Instructor",
        "level": course.get_level_display().upper(),
        "category": course.category.name if course.category else "Uncategorized",
        "duration": course.duration_str,
        "lesson_count": sum(len(s["lessons"]) for s in curriculum),
        "rating": course.rating,
        "reviews": course.reviews_count,
        "students": course.students_count,
        "price": float(course.price),
        "original_price": float(course.original_price),
        "image": course.thumbnail.url if course.thumbnail else "",
        "is_wishlisted": False,
        "curriculum": curriculum
    }
    
    return success_response(data=data)
