from typing import Optional
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from core.permissions import AuthBearer
from core.responses import success_response, StandardResponse
from core.idempotency import idempotent

from .models import Course, Category, Banner, Enrollment, UserProgress, Lesson, Review, Section
from .schemas import (
    HomeDataSchema,
    ExploreResponseSchema,
    MyCoursesResponseSchema,
    CourseDetailSchema,
    LessonCreateIn,
    LessonOut,
    PresignedURLOut,
)

import uuid
import boto3
from django.conf import settings

router = Router()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INSTRUCTOR_PALETTE = [
    [0xFF6A1B9A, 0xFFAB47BC],
    [0xFF1565C0, 0xFF42A5F5],
    [0xFF2E7D32, 0xFF66BB6A],
    [0xFFE65100, 0xFFFFA726],
    [0xFF37474F, 0xFF78909C],
]


def _s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION,
    )


def _s3_public_url(key: str) -> str:
    return (
        f'https://{settings.AWS_STORAGE_BUCKET_NAME}'
        f'.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}'
    )


def _parse_color(hex_str: str, fallback: int = 0xFF6A1B9A) -> int:
    """Convert stored '0xFF6A1B9A' string to ARGB int."""
    try:
        return int(hex_str, 16)
    except (ValueError, TypeError):
        return fallback


def _course_to_card(course, progress: Optional[float] = None) -> dict:
    """Serialize a Course ORM object to the CourseSummary shape."""
    return {
        'id': str(course.id),
        'title': course.title,
        'instructor': course.get_instructor_name(),
        'category': course.category.name if course.category else 'Uncategorized',
        'image': course.get_thumbnail_url(),
        'progress': progress,
        'badge': course.badge,
        'discount': course.discount,
        'rating': course.rating,
        'reviews': course.reviews_count,
        'price': int(course.price),
        'original_price': int(course.original_price),
        'level': course.get_level_display(),   # "Beginner" / "Intermediate" / "Advanced"
    }


# ---------------------------------------------------------------------------
# Presigned URL & Lesson creation (admin / uploader only)
# ---------------------------------------------------------------------------

@router.get('/presigned-url', response={200: StandardResponse}, auth=AuthBearer())
@idempotent(timeout=60)
def get_presigned_url(request, filename: str, content_type: str):
    """Return a one-time S3 presigned PUT URL + the key to reference later."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
    s3_key = f'lessons/videos/{uuid.uuid4()}.{ext}'

    url = _s3_client().generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': s3_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600,
    )
    return success_response(data={'upload_url': url, 's3_key': s3_key})


@router.post('/lessons', response={200: StandardResponse}, auth=AuthBearer())
def create_lesson(request, payload: LessonCreateIn):
    """Called after S3 upload succeeds. Creates the Lesson row."""
    section = get_object_or_404(Section, id=payload.section_id)
    video_url = _s3_public_url(payload.s3_key)

    lesson = Lesson.objects.create(
        section=section,
        title=payload.title,
        video_url=video_url,
        s3_key=payload.s3_key,
        file_size=payload.file_size,
        duration_str=payload.duration_str,
        order=payload.order,
        is_preview=payload.is_preview,
        upload_status='ready',
    )

    return success_response(
        message='Lesson created successfully.',
        data={
            'id': str(lesson.id),
            'title': lesson.title,
            'duration': lesson.duration_str,
            'video_url': lesson.video_url,
            's3_key': lesson.s3_key,
            'is_preview': lesson.is_preview,
            'is_completed': False,
            'upload_status': lesson.upload_status,
        },
    )


# ---------------------------------------------------------------------------
# GET /courses/home
# ---------------------------------------------------------------------------

@router.get('/home', response={200: StandardResponse}, auth=AuthBearer())
def get_home_data(request):
    user = request.auth

    # Categories
    categories = ['All'] + list(
        Category.objects.order_by('order').values_list('name', flat=True)
    )

    # Banners
    banners = []
    for b in Banner.objects.filter(is_active=True).order_by('order'):
        banners.append({
            'title': b.title,
            'subtitle': b.subtitle,
            'badge': b.badge,
            'image': b.image.url if b.image else '',
            'colors': [_parse_color(b.color_start), _parse_color(b.color_end)],
        })

    # Featured courses
    featured_qs = (
        Course.objects.filter(is_published=True, is_featured=True)
        .select_related('instructor', 'category')
    )
    featured_courses = [_course_to_card(c) for c in featured_qs]

    # Continue learning — enrolled courses with real progress
    continue_learning = []
    enrollments = (
        Enrollment.objects.filter(user=user)
        .select_related('course__instructor', 'course__category')
        .order_by('-enrolled_at')[:10]
    )
    for enrollment in enrollments:
        progress = enrollment.compute_progress()
        if progress < 1.0:
            continue_learning.append(_course_to_card(enrollment.course, progress=progress))

    # Instructors — deduplicated from published courses, with avatar initials
    seen_instructor_ids = set()
    instructors = []
    instructor_qs = (
        Course.objects.filter(is_published=True)
        .select_related('instructor')
        .exclude(instructor=None)
    )
    for idx, course in enumerate(instructor_qs):
        instr = course.instructor
        if instr.id not in seen_instructor_ids:
            seen_instructor_ids.add(instr.id)
            name = instr.get_full_name() or instr.username
            palette = INSTRUCTOR_PALETTE[len(instructors) % len(INSTRUCTOR_PALETTE)]
            instructors.append({
                'name': name,
                'initial': name[0].upper() if name else '?',
                'colors': palette,
            })

    data = {
        'categories': categories,
        'banners': banners,
        'continue_learning': continue_learning,
        'featured_courses': featured_courses,
        'instructors': instructors,
    }
    return success_response(data=data, message='Home data fetched successfully.')


# ---------------------------------------------------------------------------
# GET /courses/explore
# ---------------------------------------------------------------------------

@router.get('/explore', response={200: StandardResponse}, auth=AuthBearer())
def get_explore(
    request,
    query: Optional[str] = None,
    category: Optional[str] = None,
    filter: Optional[str] = None,
):
    """
    Browse all published courses.
    - query: full-text search on title
    - category: filter by category name ("All" = no filter)
    - filter: "Beginner" | "Intermediate" | "Advanced" | "Popular" | "Paid"
    """
    qs = Course.objects.filter(is_published=True).select_related('instructor', 'category')

    if query:
        qs = qs.filter(title__icontains=query)

    if category and category != 'All':
        qs = qs.filter(category__name__iexact=category)

    if filter and filter != 'All':
        level_map = {
            'beginner': Course.Level.BEGINNER,
            'intermediate': Course.Level.INTERMEDIATE,
            'advanced': Course.Level.ADVANCED,
        }
        filter_lower = filter.lower()
        if filter_lower in level_map:
            qs = qs.filter(level=level_map[filter_lower])
        elif filter_lower == 'popular':
            qs = qs.filter(reviews_count__gte=100).order_by('-reviews_count')
        elif filter_lower == 'paid':
            qs = qs.filter(price__gt=0)

    categories = ['All'] + list(
        Category.objects.order_by('order').values_list('name', flat=True)
    )

    data = {
        'courses': [_course_to_card(c) for c in qs],
        'categories': categories,
        'filters': ['All', 'Beginner', 'Intermediate', 'Advanced', 'Popular', 'Paid'],
    }
    return success_response(data=data, message='Courses fetched successfully.')


# ---------------------------------------------------------------------------
# GET /courses/my-courses
# ---------------------------------------------------------------------------

@router.get('/my-courses', response={200: StandardResponse}, auth=AuthBearer())
def get_my_courses(request):
    """Returns courses the authenticated user is enrolled in, split by progress."""
    user = request.auth

    enrollments = (
        Enrollment.objects.filter(user=user)
        .select_related('course__instructor', 'course__category')
        .order_by('-enrolled_at')
    )

    ongoing = []
    completed = []

    for enrollment in enrollments:
        progress = enrollment.compute_progress()
        card = _course_to_card(enrollment.course, progress=progress)
        if progress >= 1.0:
            completed.append(card)
        else:
            ongoing.append(card)

    data = {
        'ongoing': ongoing,
        'completed': completed,
        'total_enrolled': len(ongoing) + len(completed),
        'total_certificates': len(completed),
    }
    return success_response(data=data, message='My courses fetched successfully.')


# ---------------------------------------------------------------------------
# GET /courses/{course_id}
# ---------------------------------------------------------------------------

@router.get('/{course_id}', response={200: StandardResponse}, auth=AuthBearer())
def get_course_detail(request, course_id: str):
    user = request.auth

    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category')
        .prefetch_related('sections__lessons', 'reviews__user'),
        id=course_id,
    )

    # Compute per-lesson completion for this user in one query
    lesson_ids = list(
        Lesson.objects.filter(section__course=course).values_list('id', flat=True)
    )
    completed_lesson_ids = set(
        UserProgress.objects.filter(
            user=user, lesson_id__in=lesson_ids, completed=True
        ).values_list('lesson_id', flat=True)
    )

    # Build curriculum
    curriculum = []
    for section in course.sections.all():
        lessons = []
        for lesson in section.lessons.all():
            lessons.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'duration': lesson.duration_str,
                'video_url': lesson.video_url,
                'is_preview': lesson.is_preview,
                'is_completed': lesson.id in completed_lesson_ids,
            })
        curriculum.append({
            'id': str(section.id),
            'title': section.title,
            'lessons': lessons,
        })

    # Is wishlisted — extend if you add a Wishlist model later
    is_wishlisted = False

    # Reviews
    reviews_list = []
    for review in course.reviews.all()[:20]:
        reviews_list.append({
            'id': str(review.id),
            'name': review.get_reviewer_name(),
            'avatar': review.get_reviewer_initial(),
            'rating': review.rating,
            'comment': review.comment,
            'date': review.get_date_display(),
        })

    # Instructor avatar (use first_name initial for now)
    instructor_avatar = ''
    if course.instructor:
        instructor_avatar = ''  # extend when User.avatar field is added

    data = {
        'id': str(course.id),
        'title': course.title,
        'description': course.description,
        'instructor': course.get_instructor_name(),
        'instructor_avatar': instructor_avatar,
        'instructor_role': course.instructor_role,
        'level': course.get_level_display(),
        'category': course.category.name if course.category else 'Uncategorized',
        'duration': course.duration_str,
        'lesson_count': sum(len(s['lessons']) for s in curriculum),
        'rating': course.rating,
        'reviews': course.reviews_count,
        'students': course.students_count,
        'price': int(course.price),
        'original_price': int(course.original_price),
        'image': course.get_thumbnail_url(),
        'is_wishlisted': is_wishlisted,
        'curriculum': curriculum,
        'reviews_list': reviews_list,
    }
    return success_response(data=data, message='Course detail fetched successfully.')


# ---------------------------------------------------------------------------
# GET /courses/admin/reviews
# ---------------------------------------------------------------------------

@router.get('/admin/reviews', response={200: StandardResponse}, auth=AuthBearer())
def get_all_reviews(request):
    """
    Fetch all reviews across all courses for the Admin Panel.
    """
    user = request.auth
    if not (user.is_staff or user.is_superuser):
        raise HttpError(403, "Not authorized.")

    qs = Review.objects.all().select_related('course', 'user').order_by('-created_at')
    
    reviews_list = []
    for review in qs:
        reviews_list.append({
            'id': str(review.id),
            'course_id': str(review.course.id),
            'course_title': review.course.title,
            'name': review.get_reviewer_name(),
            'avatar': review.get_reviewer_initial(),
            'rating': review.rating,
            'comment': review.comment,
            'date': review.get_date_display(),
        })

    return success_response(data={'reviews': reviews_list}, message='All reviews fetched successfully.')
