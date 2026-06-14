import json
import logging
import time
from urllib.parse import unquote

from django.conf import settings

logger = logging.getLogger('art_backend')


class ApiLoggingMiddleware:
    """
    Log every request/response pair with method, path, status, duration,
    and a truncated summary of the body. Sensitive fields are redacted.
    """

    SENSITIVE_KEYS = {'password', 'token', 'access_token', 'refresh_token',
                      'id_token', 'firebase_token', 'secret', 'authorization'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip logging for static/media files and admin
        path = request.path_info
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/admin/'):
            return self.get_response(request)

        # Record start time
        start = time.time()

        # Read & redact request body
        req_body = self._safe_read_body(request)
        req_body = self._redact_sensitive(req_body)

        # Process the request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = int((time.time() - start) * 1000)

        # Read & redact response body (only for non-streaming)
        res_body = ''
        if hasattr(response, 'content') and response.get('Content-Type', '').startswith('application/json'):
            try:
                raw = response.content
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8', errors='replace')
                res_body = self._truncate_json(raw, 500)
                res_body = self._redact_sensitive(res_body)
            except Exception:
                res_body = '<unreadable>'

        log_data = {
            'method': request.method,
            'path': unquote(path),
            'status': response.status_code,
            'duration_ms': duration_ms,
            'user': str(getattr(request, 'auth', None) or request.user.id if request.user.is_authenticated else 'anonymous'),
            'query': dict(request.GET.items()) if request.GET else None,
            'request_body': req_body,
            'response_body': res_body,
        }

        # WARN for slow requests (>= 2 seconds in dev, 1 second in prod)
        threshold = 2000 if settings.DEBUG else 1000
        if duration_ms >= threshold:
            logger.warning(f'SLOW API: {log_data["method"]} {log_data["path"]} took {duration_ms}ms', extra=log_data)
        elif response.status_code >= 500:
            logger.error(f'API 5xx: {log_data["method"]} {log_data["path"]}', extra=log_data)
        elif response.status_code >= 400:
            logger.warning(f'API 4xx: {log_data["method"]} {log_data["path"]}', extra=log_data)
        else:
            logger.info(f'API: {log_data["method"]} {log_data["path"]} {response.status_code}', extra=log_data)

        return response

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_read_body(request):
        """Read and return request body without consuming it."""
        if not hasattr(request, 'body') or not request.body:
            return None
        try:
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8', errors='replace')
            # Try JSON parse for truncation
            parsed = json.loads(body)
            return json.dumps(parsed, ensure_ascii=False)[:1000]
        except (ValueError, AttributeError):
            return str(body)[:500]

    @staticmethod
    def _truncate_json(raw: str, max_len: int = 500) -> str:
        """Truncate a JSON string intelligently."""
        if len(raw) <= max_len:
            return raw
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, ensure_ascii=False)[:max_len] + '...'
        except (ValueError, TypeError):
            return raw[:max_len] + '...'

    @staticmethod
    def _redact_sensitive(value):
        """Replace values of sensitive keys with '***'."""
        if not value or not isinstance(value, str):
            return value
        try:
            parsed = json.loads(value)
            redacted = _redact_dict(parsed)
            return json.dumps(redacted, ensure_ascii=False)
        except (ValueError, TypeError):
            return value


def _redact_dict(obj):
    """Recursively redact sensitive keys in a dict/list structure."""
    if isinstance(obj, dict):
        return {
            k: '***' if k.lower() in ApiLoggingMiddleware.SENSITIVE_KEYS else _redact_dict(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_dict(item) for item in obj]
    return obj
