from ninja import NinjaAPI
from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.health import router as health_router
# pyrefly: ignore [missing-import]
from apps.accounts.api import router as accounts_router
# pyrefly: ignore [missing-import]
from apps.devices.api import router as devices_router
# pyrefly: ignore [missing-import]
from apps.courses.api import router as courses_router
# pyrefly: ignore [missing-import]
from apps.payments.api import router as payments_router
from core.exceptions import APIError
import logging

logger = logging.getLogger("art_backend")

api = NinjaAPI(
    title="ART API",
    version="1.0.0",
    description="Art Learning Platform API",
    urls_namespace="api-v1",
)

@api.exception_handler(APIError)
def api_error_handler(request, exc):
    logger.error(f"API Error: {exc.message} (Status: {exc.status_code})")
    return api.create_response(
        request,
        {"success": False, "error": {"code": f"ERR_{exc.status_code}", "message": exc.message}},
        status=exc.status_code,
    )

@api.exception_handler(Exception)
def global_exception_handler(request, exc):
    logger.exception("Unhandled Exception")
    return api.create_response(
        request,
        {"success": False, "error": {"code": "ERR_500", "message": "An internal server error occurred"}},
        status=500,
    )

api.add_router("/auth", accounts_router, tags=["Authentication"])
api.add_router("/admin/devices", devices_router, tags=["Admin Devices"])
api.add_router("/courses", courses_router, tags=["Courses"])
api.add_router("/payments", payments_router, tags=["Payments"])
api.add_router("/users", users_router, tags=["Users"])
api.add_router("/health", health_router, tags=["Health"])
