import requests
from django.http import JsonResponse
from ecomm import settings
def get_access_token(request):
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    access_token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    
    # For testing, print credentials (remove in production)
    print(f"Consumer Key: {consumer_key[:10]}...")
    print(f"Consumer Secret: {consumer_secret[:10]}...")
    
    try:
        response = requests.get(access_token_url, auth=(consumer_key, consumer_secret), timeout=30)
        print(f"Access token response status: {response.status_code}")
        print(f"Access token response text: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        access_token = result.get('access_token')
        
        if access_token:
            print(f"Access token obtained: {access_token[:50]}...")
            return JsonResponse({'access_token': access_token})
        else:
            print(f"No access token in response: {result}")
            return JsonResponse({'error': 'No access token received'}, status=500)
            
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        print(f"Unexpected error in get_access_token: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)