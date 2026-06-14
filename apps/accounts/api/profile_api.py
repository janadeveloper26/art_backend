import logging

from ninja import Router
from ninja.errors import HttpError

from apps.accounts.schemas import ProfileSchema, ProfileUpdateSchema
from apps.courses.models import Enrollment
from core.permissions import AuthBearer
from core.responses import success_response, StandardResponse

logger = logging.getLogger('art_backend')

router = Router(tags=['Profile'])


def _profile_data(user):
    total_courses = Enrollment.objects.filter(user=user).count()
    completed_courses = Enrollment.objects.filter(user=user, completed_at__isnull=False).count()
    completion_rate = int((completed_courses / total_courses * 100) if total_courses > 0 else 0)
    return {
        'id': str(user.id),
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': user.phone_number,
        'avatar': None,
        'role': 'admin' if user.is_staff else 'student',
        'is_verified': user.is_approved,
        'stats': {
            'total_courses': total_courses,
            'watch_time_hours': 0.0,
            'completion_rate': completion_rate,
        },
    }


@router.get('/', response={200: StandardResponse}, auth=AuthBearer())
def get_profile(request):
    return success_response(data=_profile_data(request.auth))


@router.patch('/', response={200: StandardResponse}, auth=AuthBearer())
def update_profile(request, payload: ProfileUpdateSchema):
    user = request.auth
    if not user:
        raise HttpError(401, 'Authentication required.')
    parts = []
    if payload.name:
        user.first_name = payload.name
        parts.append('first_name')
    if payload.email:
        user.email = payload.email
        parts.append('email')
    if not parts:
        raise HttpError(400, 'No fields to update.')
    try:
        user.save(update_fields=parts)
    except Exception as e:
        logger.error('Profile update failed for user %s: %s', user.id, e)
        raise HttpError(500, 'Failed to update profile.')
    return success_response(data=_profile_data(user), message='Profile updated successfully.')
