import logging
import traceback

from django.contrib import admin
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpRequest
from django.urls import path
from ninja import NinjaAPI, Router
from ninja.errors import ValidationError
from django_ratelimit.exceptions import Ratelimited

from apps.accounts.api.auth_api import router as auth_router
from apps.accounts.api.users_api import router as users_router
from apps.accounts.api.profile_api import router as profile_router
from apps.courses.api import router as courses_router, video_router
from apps.supply.api import router as supply_router
from apps.payments.api import router as payments_router
from core.permissions import AuthBearer
from core.responses import success_response, StandardResponse, error_response

logger = logging.getLogger('art_backend')


api = NinjaAPI(
    title='ART API',
    version='1.0.0',
    docs_url='/docs',
)


# ---------------------------------------------------------------------------
# Global exception handlers — production-grade error envelope
# NOTE: Order matters — more specific handlers must be registered first.
# ---------------------------------------------------------------------------


@api.exception_handler(ValidationError)
def validation_handler(request: HttpRequest, exc: ValidationError):
    """Return a clean error envelope for schema validation failures (422)."""
    errors = exc.errors if hasattr(exc, 'errors') else []
    return api.create_response(
        request,
        error_response('VALIDATION_ERROR', str(errors)),
        status=422,
    )


@api.exception_handler(Ratelimited)
def ratelimited_handler(request: HttpRequest, exc: Ratelimited):
    """Handle rate limit exceptions."""
    logger.warning(f'Rate limit exceeded for IP: {request.META.get("REMOTE_ADDR")}')
    return api.create_response(
        request,
        error_response('TOO_MANY_REQUESTS', 'You have made too many requests. Please try again later.'),
        status=429,
    )


@api.exception_handler(ValueError)
def value_error_handler(request: HttpRequest, exc: ValueError):
    """Wrap ValueError as a 400 so callers get a structured error."""
    logger.warning('ValueError: %s', exc)
    return api.create_response(
        request,
        error_response('BAD_REQUEST', str(exc)),
        status=400,
    )


@api.exception_handler(DjangoValidationError)
def django_validation_handler(request: HttpRequest, exc: DjangoValidationError):
    """Catch Django model ValidationError (e.g. invalid UUID) as 400."""
    messages = exc.messages if hasattr(exc, 'messages') else [str(exc)]
    return api.create_response(
        request,
        error_response('VALIDATION_ERROR', '; '.join(messages)),
        status=400,
    )


from django.http import Http404

@api.exception_handler(Http404)
def http_404_handler(request: HttpRequest, exc: Http404):
    """Return 404 JSON response instead of 500."""
    return api.create_response(
        request,
        error_response('NOT_FOUND', 'The requested resource was not found.'),
        status=404,
    )

@api.exception_handler(Exception)
def global_500_handler(request: HttpRequest, exc: Exception):
    """Last-resort catch-all for unexpected errors (500)."""
    # Skip Ninja's own HttpError — let Ninja handle it natively
    from ninja.errors import HttpError
    if isinstance(exc, HttpError):
        return api.create_response(
            request,
            error_response('ERROR', str(exc)),
            status=exc.status_code,
        )

    logger.error('Unhandled exception: %s', exc, exc_info=True)
    return api.create_response(
        request,
        error_response('INTERNAL_ERROR', 'Something went wrong. Please try again later.'),
        status=500,
    )

# ---------------------------------------------------------------------------
# Inline /home router — aggregated home screen data
# ---------------------------------------------------------------------------

home_router = Router(tags=['Home'])


@home_router.get('', response={200: dict}, auth=AuthBearer())
def get_home(request):
    """
    Thin shim: delegates to the courses /home handler so the mobile app
    can reach it at /api/v1/home (not /api/v1/courses/home).
    """
    from apps.courses.api import get_home_data
    return get_home_data(request)


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

api.add_router('/auth/',    auth_router)
api.add_router('/users/',   users_router)
api.add_router('/profile/', profile_router)
api.add_router('/courses/', courses_router)
api.add_router('/videos/',  video_router)
api.add_router('/supply/',  supply_router)
api.add_router('/payments/', payments_router)
api.add_router('/home/',     home_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
]
