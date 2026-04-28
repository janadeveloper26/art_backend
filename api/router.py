from ninja import NinjaAPI
from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.health import router as health_router
from accounts.api import router as accounts_router
from courses.api import router as courses_router
from payments.api import router as payments_router
from core.exceptions import APIError
import logging

logger = logging.getLogger("art_backend")

api = NinjaAPI(
    title="ART API",
    version="1.0.0",
    description="Art Learning Platform API",
)

@api.exception_handler(APIError)
def api_error_handler(request, exc):
    logger.error(f"API Error: {exc.message} (Status: {exc.status_code})")
    return api.create_response(
        request,
        {"status": "error", "message": exc.message},
        status=exc.status_code,
    )

@api.exception_handler(Exception)
def global_exception_handler(request, exc):
    logger.exception("Unhandled Exception")
    return api.create_response(
        request,
        {"status": "error", "message": "An internal server error occurred"},
        status=500,
    )

api.add_router("/auth", accounts_router, tags=["Authentication"])
api.add_router("/courses", courses_router, tags=["Courses"])
api.add_router("/payments", payments_router, tags=["Payments"])
api.add_router("/users", users_router, tags=["Users"])
api.add_router("/health", health_router, tags=["Health"])
