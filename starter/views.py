"""HTTP views"""
import functools
import os
import secrets
import time

import jwt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import toml

# ============================================================================
# SESSION AUTH - JWT tokens for production security
# ============================================================================

SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
JWT_EXPIRY = 3600  # 1 hour


# Read frontend/dist/index.html for serving (production only)
_index_html_template = None
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist", "index.html")) as f:
        _index_html_template = f.read()
except FileNotFoundError:
    pass  # No built frontend (dev mode)


def require_session(f):
    """Decorator that validates JWT from Authorization header."""
    @functools.wraps(f)
    def decorated(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({
                "error": {
                    "type": "AuthenticationError",
                    "code": "MISSING_TOKEN",
                    "message": "Authorization header with Bearer token is required",
                }
            }, status=401)
        token = auth_header[7:]
        try:
            jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                "error": {
                    "type": "AuthenticationError",
                    "code": "INVALID_TOKEN",
                    "message": "Session expired, please refresh the page",
                }
            }, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({
                "error": {
                    "type": "AuthenticationError",
                    "code": "INVALID_TOKEN",
                    "message": "Invalid session token",
                }
            }, status=401)
        return f(request, *args, **kwargs)
    return decorated


# ============================================================================
# SESSION ROUTES - Auth endpoints (unprotected)
# ============================================================================

def serve_index(request):
    """Serve index.html (production only)."""
    if not _index_html_template:
        return HttpResponse("Frontend not built. Run make build first.", status=404)
    return HttpResponse(_index_html_template, content_type="text/html")


def get_session(request):
    """Issues a JWT session token."""
    token = jwt.encode(
        {"iat": int(time.time()), "exp": int(time.time()) + JWT_EXPIRY},
        SESSION_SECRET,
        algorithm="HS256",
    )
    return JsonResponse({"token": token})


# ============================================================================
# API ROUTES
# ============================================================================

@require_http_methods(["GET"])
def metadata(request):
    try:
        with open('deepgram.toml', 'r') as f:
            return JsonResponse(toml.load(f).get('meta', {}))
    except:
        return JsonResponse({'error': 'Failed'}, status=500)
