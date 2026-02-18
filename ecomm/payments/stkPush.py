import requests
from datetime import datetime
import json
import base64
from django.http import JsonResponse
from .genrateMpesaAcesstoken import get_access_token
from .models import Transaction
from django.views.decorators.csrf import csrf_exempt







@csrf_exempt
def initiate_stk_push(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests allowed'
        }, status=400)
    
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        phone_number = data.get('phone_number')
        amount = data.get('amount')
        order_id = data.get('order_id')
        
        # Debug logging
        print(f"Received request: phone={phone_number}, amount={amount}, order={order_id}")
        
        if not phone_number:
            return JsonResponse({
                'success': False,
                'error': 'Phone number is required'
            }, status=400)
        
        if not amount:
            return JsonResponse({
                'success': False,
                'error': 'Amount is required'
            }, status=400)
        
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Order ID is required'
            }, status=400)
        
        # Get access token
        try:
            # Create a mock request for get_access_token if needed
            from django.http import HttpRequest
            token_request = HttpRequest()
            token_request.method = 'GET'
            
            access_token_response = get_access_token(token_request)
            
            if isinstance(access_token_response, JsonResponse):
                # Get the content properly
                response_data = json.loads(access_token_response.content)
                access_token = response_data.get('access_token')
                
                if not access_token:
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to get access token'
                    }, status=500)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token service error'
                }, status=500)
                
        except Exception as e:
            print(f"Access token error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Access token error: {str(e)}'
            }, status=500)
        
        # Format phone number
        phone_number = str(phone_number).strip()
        if not phone_number.startswith('254'):
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]  # Remove +
            elif len(phone_number) == 9:
                phone_number = '254' + phone_number
        
        print(f"Formatted phone: {phone_number}")
        
        # M-Pesa API configuration
        process_request_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        callback_url = 'https://bf8f-196-96-76-134.ngrok-free.app/payments/callback/'  # Update if needed
        passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        business_short_code = '174379'
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = business_short_code + passkey + timestamp
        password = base64.b64encode(password_string.encode()).decode('utf-8')
        
        # Prepare headers and payload
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            'BusinessShortCode': business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': str(int(float(amount))),  # Convert to integer string
            'PartyA': phone_number,
            'PartyB': business_short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': f'ORDER{order_id}',
            'TransactionDesc': f'Payment for order {order_id}'
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Make STK Push request
        try:
            response = requests.post(process_request_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            
            print(f"M-Pesa Response: {json.dumps(response_data, indent=2)}")
            
            checkout_request_id = response_data.get('CheckoutRequestID')
            response_code = response_data.get('ResponseCode')
            error_message = response_data.get('errorMessage')
            
            if response_code == "0" and checkout_request_id:
                # Store checkout ID in session
                if hasattr(request, 'session'):
                    request.session[f'checkout_id_{order_id}'] = checkout_request_id
                
                # Create transaction record
                Transaction.objects.create(
                    order_id=order_id,
                    amount=amount,
                    checkout_id=checkout_request_id,
                    phone_number=phone_number,
                    status="Pending",
                    mpesa_code="Pending"
                )
                
                return JsonResponse({
                    'success': True,
                    'checkout_id': checkout_request_id,
                    'message': 'STK Push initiated successfully. Please check your phone.'
                })
            else:
                error_msg = error_message or 'STK Push failed'
                print(f"STK Push failed: {error_msg}")
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Network error: {str(e)}'
            })
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            })
            
    except Exception as e:
        print(f"Global error in initiate_stk_push: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)
