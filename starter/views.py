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
# SESSION AUTH - JWT tokens with page nonce for production security
# ============================================================================

SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
REQUIRE_NONCE = bool(os.environ.get("SESSION_SECRET"))

# In-memory nonce store: nonce -> expiry timestamp
session_nonces = {}
NONCE_TTL = 5 * 60  # 5 minutes
JWT_EXPIRY = 3600  # 1 hour


def generate_nonce():
    """Generates a single-use nonce and stores it with an expiry."""
    nonce = secrets.token_hex(16)
    session_nonces[nonce] = time.time() + NONCE_TTL
    return nonce


def consume_nonce(nonce):
    """Validates and consumes a nonce (single-use). Returns True if valid."""
    expiry = session_nonces.pop(nonce, None)
    if expiry is None:
        return False
    return time.time() < expiry


def cleanup_nonces():
    """Remove expired nonces."""
    now = time.time()
    expired = [k for k, v in session_nonces.items() if now >= v]
    for k in expired:
        del session_nonces[k]


# Read frontend/dist/index.html template for nonce injection
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
    """Serve index.html with injected session nonce (production only)."""
    if not _index_html_template:
        return HttpResponse("Frontend not built. Run make build first.", status=404)
    cleanup_nonces()
    nonce = generate_nonce()
    html = _index_html_template.replace(
        "</head>",
        f'<meta name="session-nonce" content="{nonce}">\n</head>'
    )
    return HttpResponse(html, content_type="text/html")


def get_session(request):
    """Issues a JWT. In production, requires valid nonce via X-Session-Nonce header."""
    if REQUIRE_NONCE:
        nonce = request.headers.get("X-Session-Nonce")
        if not nonce or not consume_nonce(nonce):
            return JsonResponse({
                "error": {
                    "type": "AuthenticationError",
                    "code": "INVALID_NONCE",
                    "message": "Valid session nonce required. Please refresh the page.",
                }
            }, status=403)
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
