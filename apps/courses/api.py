import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from core.permissions import AuthBearer
from core.responses import success_response, StandardResponse
from core.idempotency import idempotent

from .models import Course, Category, Banner, Enrollment, UserProgress, Lesson, Review, Section
from .schemas import CourseCreateIn, LessonCreateIn

logger = logging.getLogger(__name__)
router = Router()

INSTRUCTOR_PALETTE = [
    [0xFF6A1B9A, 0xFFAB47BC],
    [0xFF1565C0, 0xFF42A5F5],
    [0xFF2E7D32, 0xFF66BB6A],
    [0xFFE65100, 0xFFFFA726],
    [0xFF37474F, 0xFF78909C],
]

# ---------------------------------------------------------------------------
# S3 & CloudFront — cached clients
# ---------------------------------------------------------------------------

_s3 = None


def _get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION,
        )
    return _s3


_cf_signer = None
_cf_signer_expires = 0


def _get_cf_signer():
    global _cf_signer, _cf_signer_expires
    now = int(datetime.now(timezone.utc).timestamp())
    if _cf_signer is not None and now < _cf_signer_expires:
        return _cf_signer
    if not settings.CLOUDFRONT_KEY_ID or not settings.CLOUDFRONT_PRIVATE_KEY:
        _cf_signer = None
        return None

    try:
        raw_key = settings.CLOUDFRONT_PRIVATE_KEY
        pem_data = raw_key.encode() if '-----' in raw_key else open(raw_key, 'rb').read()
        private_key = serialization.load_pem_private_key(pem_data, password=None)
    except Exception as exc:
        logger.error('Failed to load CloudFront private key: %s', exc)
        _cf_signer = None
        return None

    def _rsa_signer(message):
        return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

    _cf_signer = CloudFrontSigner(settings.CLOUDFRONT_KEY_ID, _rsa_signer)
    _cf_signer_expires = now + 300
    return _cf_signer


def _s3_public_url(key: str) -> str:
    if settings.CLOUDFRONT_DOMAIN:
        return f'https://{settings.CLOUDFRONT_DOMAIN}/{key}'
    return (
        f'https://{settings.AWS_STORAGE_BUCKET_NAME}'
        f'.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}'
    )


def _cloudfront_signed_url(key: str, expires_in: int = 3600) -> str:
    cf_domain = settings.CLOUDFRONT_DOMAIN
    if not cf_domain:
        return _get_s3().generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires_in,
        )

    signer = _get_cf_signer()
    if signer is None:
        logger.warning('CloudFront domain set but no signing keys — falling back to S3 presigned URL')
        return _get_s3().generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires_in,
        )

    url = f'https://{cf_domain}/{key}'
    return signer.generate_presigned_url(
        url, date_less_than=datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    )


def _parse_color(hex_str: str, fallback: int = 0xFF6A1B9A) -> int:
    try:
        return int(hex_str, 16)
    except (ValueError, TypeError):
        return fallback


def _course_to_card(course, progress: Optional[float] = None) -> dict:
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
        'level': course.get_level_display(),
    }


def _build_course(payload, user) -> Course:
    if not payload.title or not payload.title.strip():
        raise HttpError(400, 'title is required.')

    category = None
    if payload.category_id:
        try:
            uuid.UUID(payload.category_id)
        except (ValueError, AttributeError):
            raise HttpError(400, f'Invalid category_id: {payload.category_id}')
        category = get_object_or_404(Category, id=payload.category_id)

    try:
        price = float(payload.price)
    except (ValueError, TypeError):
        price = 0.0

    original_price = price
    if payload.original_price:
        try:
            original_price = float(payload.original_price)
        except (ValueError, TypeError):
            pass

    course = Course.objects.create(
        title=payload.title.strip(),
        description=payload.description.strip(),
        category=category,
        instructor=user,
        instructor_role=payload.instructor_role or 'Instructor',
        price=price,
        original_price=original_price,
        level=payload.level.upper() if payload.level else 'BEGINNER',
        is_published=payload.is_published,
        is_featured=payload.is_featured,
    )
    logger.info('Course created: %s by user %s', course.id, user.id)
    return course


@router.get('/presigned-url', response={200: StandardResponse}, auth=AuthBearer())
@idempotent(timeout=60)
def get_presigned_url(request, filename: str, content_type: str):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
    s3_key = f'lessons/videos/{uuid.uuid4()}.{ext}'
    url = _get_s3().generate_presigned_url(
        'put_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key, 'ContentType': content_type},
        ExpiresIn=3600,
    )
    return success_response(data={'upload_url': url, 's3_key': s3_key})


@router.post('/lessons', response={200: StandardResponse}, auth=AuthBearer())
def create_lesson(request, payload: LessonCreateIn):
    section = get_object_or_404(Section, id=payload.section_id)
    lesson = Lesson.objects.create(
        section=section,
        title=payload.title,
        video_url=_s3_public_url(payload.s3_key),
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


@router.get('/categories', response={200: StandardResponse}, auth=AuthBearer())
def get_course_categories(request):
    categories = ['All'] + list(Category.objects.order_by('order').values_list('name', flat=True))
    return success_response(data=categories, message='Categories fetched successfully.')


@router.get('/home', response={200: StandardResponse}, auth=AuthBearer())
def get_home_data(request):
    user = request.auth
    categories = ['All'] + list(Category.objects.order_by('order').values_list('name', flat=True))

    banners = [
        {
            'title': b.title,
            'subtitle': b.subtitle,
            'badge': b.badge,
            'image': b.image.url if b.image else '',
            'colors': [_parse_color(b.color_start), _parse_color(b.color_end)],
        }
        for b in Banner.objects.filter(is_active=True).order_by('order')
    ]

    featured_qs = Course.objects.filter(is_published=True, is_featured=True).select_related('instructor', 'category')
    featured_courses = [_course_to_card(c) for c in featured_qs]

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

    seen_ids = set()
    instructors = []
    for idx, course in enumerate(
        Course.objects.filter(is_published=True).select_related('instructor').exclude(instructor=None)
    ):
        instr = course.instructor
        if instr.id not in seen_ids:
            seen_ids.add(instr.id)
            name = instr.get_full_name() or instr.username
            palette = INSTRUCTOR_PALETTE[len(instructors) % len(INSTRUCTOR_PALETTE)]
            instructors.append({
                'name': name,
                'initial': name[0].upper() if name else '?',
                'colors': palette,
            })

    return success_response(
        data={
            'categories': categories,
            'banners': banners,
            'continue_learning': continue_learning,
            'featured_courses': featured_courses,
            'instructors': instructors,
        },
        message='Home data fetched successfully.',
    )


LEVEL_MAP = {
    'beginner': Course.Level.BEGINNER,
    'intermediate': Course.Level.INTERMEDIATE,
    'advanced': Course.Level.ADVANCED,
}


@router.get('/explore', response={200: StandardResponse}, auth=AuthBearer())
def get_explore(
    request,
    query: Optional[str] = None,
    category: Optional[str] = None,
    level_filter: Optional[str] = None,
):
    qs: QuerySet = Course.objects.filter(is_published=True).select_related('instructor', 'category')

    if query:
        qs = qs.filter(title__icontains=query)
    if category and category != 'All':
        qs = qs.filter(category__name__iexact=category)
    if level_filter and level_filter != 'All':
        key = level_filter.lower()
        if key in LEVEL_MAP:
            qs = qs.filter(level=LEVEL_MAP[key])
        elif key == 'popular':
            qs = qs.filter(reviews_count__gte=100).order_by('-reviews_count')
        elif key == 'paid':
            qs = qs.filter(price__gt=0)

    categories = ['All'] + list(Category.objects.order_by('order').values_list('name', flat=True))

    return success_response(
        data={
            'courses': [_course_to_card(c) for c in qs],
            'categories': categories,
            'filters': ['All', 'Beginner', 'Intermediate', 'Advanced', 'Popular', 'Paid'],
        },
        message='Courses fetched successfully.',
    )


@router.get('/my-courses', response={200: StandardResponse}, auth=AuthBearer())
def get_my_courses(request):
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
        (completed if progress >= 1.0 else ongoing).append(card)

    return success_response(
        data={
            'ongoing': ongoing,
            'completed': completed,
            'total_enrolled': len(ongoing) + len(completed),
            'total_certificates': len(completed),
        },
        message='My courses fetched successfully.',
    )


@router.get('/admin/reviews', response={200: StandardResponse}, auth=AuthBearer())
def get_all_reviews(request):
    user = request.auth
    if not (user.is_staff or user.is_superuser):
        raise HttpError(403, 'Not authorized.')

    reviews = [
        {
            'id': str(r.id),
            'course_id': str(r.course.id),
            'course_title': r.course.title,
            'name': r.get_reviewer_name(),
            'avatar': r.get_reviewer_initial(),
            'rating': r.rating,
            'comment': r.comment,
            'date': r.get_date_display(),
        }
        for r in Review.objects.select_related('course', 'user').order_by('-created_at')
    ]
    return success_response(data={'reviews': reviews}, message='All reviews fetched successfully.')


@router.post('', response={200: StandardResponse}, auth=AuthBearer())
def create_course_root(request, payload: CourseCreateIn):
    user = request.auth
    if not (user.is_staff or user.is_superuser):
        raise HttpError(403, 'Only staff or superadmin can create courses.')
    course = _build_course(payload, user)
    return success_response(
        data={'id': str(course.id), 'title': course.title},
        message='Course created successfully.',
    )


@router.post('/admin', response={200: StandardResponse}, auth=AuthBearer())
def create_course(request, payload: CourseCreateIn):
    user = request.auth
    if not user.is_superuser:
        raise HttpError(403, 'Only superadmin can create courses.')
    course = _build_course(payload, user)
    return success_response(
        data={'id': str(course.id), 'title': course.title},
        message='Course created successfully.',
    )


@router.get('/{course_id}', response={200: StandardResponse}, auth=AuthBearer())
def get_course_detail(request, course_id: str):
    user = request.auth
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category')
        .prefetch_related('sections__lessons', 'reviews__user'),
        id=course_id,
    )

    lesson_ids = list(Lesson.objects.filter(section__course=course).values_list('id', flat=True))
    completed_ids = set(
        UserProgress.objects.filter(user=user, lesson_id__in=lesson_ids, completed=True)
        .values_list('lesson_id', flat=True)
    )

    curriculum = []
    for section in course.sections.all():
        lessons = [
            {
                'id': str(lesson.id),
                'title': lesson.title,
                'duration': lesson.duration_str,
                'video_url': lesson.video_url,
                'is_preview': lesson.is_preview,
                'is_completed': lesson.id in completed_ids,
            }
            for lesson in section.lessons.all()
        ]
        curriculum.append({'id': str(section.id), 'title': section.title, 'lessons': lessons})

    reviews_list = [
        {
            'id': str(r.id),
            'name': r.get_reviewer_name(),
            'avatar': r.get_reviewer_initial(),
            'rating': r.rating,
            'comment': r.comment,
            'date': r.get_date_display(),
        }
        for r in course.reviews.all()[:20]
    ]

    return success_response(
        data={
            'id': str(course.id),
            'title': course.title,
            'description': course.description,
            'instructor': course.get_instructor_name(),
            'instructor_avatar': '',
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
            'is_wishlisted': False,
            'curriculum': curriculum,
            'sections': curriculum,
            'reviews_list': reviews_list,
        },
        message='Course detail fetched successfully.',
    )


# Video signed-url router (mounted at /api/v1/videos/)


class SignedUrlIn(Schema):
    file_name: str


video_router = Router(tags=['Videos'])


@video_router.post('/signed-url', response={200: StandardResponse}, auth=AuthBearer())
def get_signed_url(request, payload: SignedUrlIn):
    key = payload.file_name
    if not key.startswith('lessons/videos/'):
        key = f'lessons/videos/{key}'
    try:
        url = _cloudfront_signed_url(key, expires_in=3600)
    except Exception as exc:
        logger.error('Failed to generate signed URL for %s: %s', key, exc)
        raise HttpError(502, 'Failed to generate video URL.')
    logger.info('Signed URL generated for key=%s length=%s', key, len(url))
    return success_response(data={'url': url})
