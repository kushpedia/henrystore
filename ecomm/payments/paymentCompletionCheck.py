# views.py - Add this function
from django.http import JsonResponse
from .models import Transaction
from core.models import CartOrder
def check_payment_status(request, order_id):
    """Check if a payment has been completed for an order"""
    try:
        order = CartOrder.objects.get(oid=order_id)
        
        
        checkout_id = request.session.get(f'checkout_id_{order_id}')
        
        if checkout_id:
            transaction = Transaction.objects.filter(
                checkout_id=checkout_id,
                status="Success"
            ).first()
            
            if transaction:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment completed successfully',
                    'transaction_id': transaction.mpesa_code
                })
        
        # Check for any pending transaction
        transaction = Transaction.objects.filter(
            phone_number__contains=order.phone if hasattr(order, 'phone') else '',
            status__in=['Pending', 'Processing']
        ).first()
        
        if transaction:
            return JsonResponse({
                'status': 'pending',
                'message': 'Payment is being processed'
            })
        
        return JsonResponse({
            'status': 'pending',
            'message': 'Waiting for payment...'
        })
        
    except CartOrder.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)