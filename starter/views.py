"""HTTP views"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import toml

@require_http_methods(["GET"])
def metadata(request):
    try:
        with open('deepgram.toml', 'r') as f:
            return JsonResponse(toml.load(f).get('meta', {}))
    except:
        return JsonResponse({'error': 'Failed'}, status=500)
