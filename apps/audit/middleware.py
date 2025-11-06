from django.utils.deprecation import MiddlewareMixin
from .utils import write_audit

class AuditMiddleware(MiddlewareMixin):
    SAFE = {"GET", "HEAD", "OPTIONS"}
    EXCLUDE_PREFIXES = ("/static/", "/admin/js/", "/api/schema",)
    EXCLUDE_PATHS = {"/admin/login/"}

    SENSITIVE_KEYS = {"password", "csrfmiddlewaretoken"}

    def process_response(self, request, response):
        try:
            method = request.method.upper()
            path = request.path

            if method in self.SAFE:
                return response
            if any(path.startswith(p) for p in self.EXCLUDE_PREFIXES) or path in self.EXCLUDE_PATHS:
                return response
            if getattr(response, "status_code", 200) >= 500:
                return response  # don't double log server errors here

            body = {}
            if hasattr(request, "POST"):
                for k, v in request.POST.items():
                    body[k] = "***" if k.lower() in self.SENSITIVE_KEYS else v

            write_audit(
                request=request,
                action=f"http.{method.lower()}",
                message=f"{path} -> {response.status_code}",
                level="info",
                extra={"path": path, "status": response.status_code, "post": body}
            )
        finally:
            return response

class ClientIPMiddleware:
    """
    Adds request.client_ip using X-Forwarded-For if present, otherwise REMOTE_ADDR.
    Put this *before* AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            request.client_ip = xff.split(",")[0].strip()
        else:
            request.client_ip = request.META.get("REMOTE_ADDR", "")
        return self.get_response(request)
