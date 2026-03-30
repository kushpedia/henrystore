import requests
from django.http import JsonResponse
from ecomm import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_access_token(request):
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    access_token_url = settings.MPESA_ACCESS_TOKEN_URL    
    try:
        response = requests.get(access_token_url, auth=(consumer_key, consumer_secret), timeout=30)        
        response.raise_for_status()
        result = response.json()
        access_token = result.get('access_token')
                
        if access_token:        
            return JsonResponse({'access_token': access_token})
        else:            
            return JsonResponse({'error': 'No access token received'}, status=500)
            
    except requests.exceptions.RequestException as e:
        
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        
        return JsonResponse({'error': str(e)}, status=500)