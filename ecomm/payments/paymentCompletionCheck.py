# views.py - Enhanced status check view
from django.http import JsonResponse
from .models import Transaction
import logging
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

@csrf_exempt
def check_payment_status(request, order_id):
    """Check payment status with error details"""
    try:
        checkout_id = request.GET.get('checkout_id')
        
        if checkout_id:
            try:
                transaction = Transaction.objects.get(checkout_id=checkout_id)
                return get_transaction_response(transaction)
            except Transaction.DoesNotExist:
                # Check if there's any transaction for this order
                transactions = Transaction.objects.filter(order_id=order_id).order_by('-timestamp')
                if transactions.exists():
                    return get_transaction_response(transactions.first())
                
                return JsonResponse({
                    'status': 'pending',
                    'message': 'Payment request sent. Waiting for response...',
                    'action': 'wait'
                })
        
        # Check by order_id
        transactions = Transaction.objects.filter(order_id=order_id).order_by('-timestamp')
        
        if transactions.exists():
            return get_transaction_response(transactions.first())
        
        return JsonResponse({
            'status': 'not_initiated',
            'message': 'No payment initiated yet.',
            'action': 'initiate'
        })
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error checking payment status',
            'action': 'retry'
        }, status=500)

@csrf_exempt
def get_transaction_response(transaction):
    """Format transaction data for frontend"""
    
    status_map = {
        'Success': 'success',
        'Failed': 'failed',
        'Cancelled': 'cancelled',
        'Expired': 'expired',
        'Pending': 'pending',
        'Processing': 'processing'
    }
    
    response = {
        'status': status_map.get(transaction.status, 'pending'),
        'transaction_id': transaction.mpesa_code or transaction.checkout_id,
        'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
    }
    
    # Add status-specific info
    if transaction.status == 'Success':
        response.update({
            'message': 'Payment completed successfully!',
            'action': 'redirect',
            'redirect_url': f'/payment-completed/{transaction.order_id}/?method=mpesa&code={transaction.mpesa_code}'
        })
    elif transaction.status == 'Failed':
        # Include detailed error info
        response.update({
            'message': transaction.result_desc or 'Payment failed',
            'user_message': get_user_friendly_error(transaction.result_code, transaction.result_desc),
            'action': transaction.user_action or 'retry',
            'error_code': transaction.result_code,
            'error_category': transaction.error_category,
            'suggested_action': get_suggested_action(transaction.result_code)
        })
    elif transaction.status in ['Pending', 'Processing']:
        response.update({
            'message': 'Waiting for payment confirmation...',
            'action': 'wait'
        })
    
    return JsonResponse(response)


@csrf_exempt
def get_user_friendly_error(result_code, result_desc):
    """Convert error code to user-friendly message"""
    error_map = {
        1: "Insufficient balance in your M-PESA account. Please check your balance and try again.",
        1032: "You cancelled the payment request. Please try again when ready.",
        2001: "Incorrect M-PESA PIN entered. Please try again with the correct PIN.",
        1019: "Payment request expired. Please initiate a new payment.",
        1037: "Unable to reach your phone. Please ensure it's connected and try again.",
        2: "Amount is less than minimum allowed. Please check the amount.",
        3: "Amount exceeds maximum allowed. Please check the amount.",
        4: "Transaction would exceed daily limit. Please try again tomorrow.",
        5: "Transaction would exceed minimum balance.",
        6: "Sender information is invalid.",
        7: "Receiver information is invalid.",
        8: "Transaction would exceed maximum balance.",
        9: "M-PESA system is temporarily unavailable. Please try again later.",
        10: "Transaction timeout. Please try again.",
        11: "Duplicate transaction detected.",
    }
    
    return error_map.get(result_code, result_desc or "Payment failed. Please try again.")


@csrf_exempt
def get_suggested_action(result_code):
    """Get suggested action based on error"""
    action_map = {
        1: "Please check your M-PESA balance and ensure you have sufficient funds.",
        1032: "Please ensure you're ready to complete the payment before trying again.",
        2001: "Double-check your M-PESA PIN before entering.",
        1019: "Payment requests expire after a few minutes. Please start a new payment.",
        1037: "Ensure your phone has network coverage and is not in airplane mode.",
        9: "This is a temporary system issue. Please wait a few minutes and try again.",
    }
    
    return action_map.get(result_code, "Please try again or contact customer support.")

