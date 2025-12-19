# mpesaPayCallback.py - Update with better error logging
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction
from core.models import CartOrder

logger = logging.getLogger(__name__)


MPESA_RESULT_CODES = {
    0: ("Success", "Transaction completed successfully"),
    1: ("Insufficient Balance", "Insufficient funds in M-PESA account"),
    2: ("Less Than Minimum", "Amount is less than the minimum allowed"),
    3: ("More Than Maximum", "Amount is more than the maximum allowed"),
    4: ("Would Exceed Daily Limit", "Transaction would exceed daily limit"),
    5: ("Would Exceed Minimum Balance", "Transaction would exceed minimum balance"),
    6: ("Unresolved Primary Party", "Primary party (sender) is unresolved"),
    7: ("Unresolved Receiver Party", "Receiver party is unresolved"),
    8: ("Would Exceed Maximum Balance", "Transaction would exceed maximum balance"),
    9: ("System Unavailable", "M-PESA system is unavailable"),
    10: ("Timeout", "Transaction timeout"),
    11: ("Duplicate", "Duplicate transaction"),
    12: ("Invalid Reference", "Invalid transaction reference"),
    13: ("Invalid Amount", "Invalid transaction amount"),
    14: ("Invalid Sender", "Invalid sender information"),
    15: ("Invalid Receiver", "Invalid receiver information"),
    16: ("Other Error", "Other error occurred"),
    17: ("Would Exceed Transfer Limit", "Would exceed transfer limit"),
    18: ("Would Exceed Aggregate Limit", "Would exceed aggregate limit"),
    20: ("Debit Account Invalid", "Debit account is invalid"),
    26: ("Unsupported Transaction", "Transaction type not supported"),
    29: ("Invalid Third Party Reference", "Invalid third party reference"),
    40: ("Reversal Successful", "Reversal successful"),
    41: ("No Reverse Found", "No reverse transaction found"),
    42: ("Reversal Already Done", "Reversal already done"),
    1019: ("Transaction Expired", "Transaction has expired"),
    1032: ("Cancelled by User", "Request cancelled by user"),
    1037: ("User Unreachable", "Customer cannot be reached"),
    2001: ("Invalid PIN", "Incorrect M-PESA PIN entered"),
}

@csrf_exempt
def payment_callback(request):
    """Handle M-Pesa STK Push callback"""
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests are allowed")
    
    # Log the raw request body for debugging
    raw_body = request.body.decode('utf-8')
    logger.info(f"Raw callback received: {raw_body}")
    
    try:
        callback_data = json.loads(raw_body)
        logger.info(f"Parsed callback data: {json.dumps(callback_data, indent=2)}")
        
        # Extract required information
        stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc", "No description")
        checkout_id = stk_callback.get("CheckoutRequestID")
        
        logger.info(f"Callback details - Code: {result_code}, Desc: {result_desc}, CheckoutID: {checkout_id}")
        
        if not checkout_id:
            logger.error("Missing CheckoutRequestID in callback")
            return JsonResponse({
                "ResultCode": 1,
                "ResultDesc": "Missing CheckoutRequestID"
            })
        
        # Find or create transaction
        try:
            transaction = Transaction.objects.get(checkout_id=checkout_id)
            logger.info(f"Found transaction: {transaction.id}")
        except Transaction.DoesNotExist:
            logger.warning(f"No transaction found for checkout_id: {checkout_id}")
            # Create a new transaction if not found
            transaction = Transaction.objects.create(
                checkout_id=checkout_id,
                status="Failed" if result_code != 0 else "Success",
                result_code=result_code,
                result_desc=result_desc
            )
        
        # Handle based on result code
        if result_code == 0:
            # SUCCESS
            return handle_success_callback(stk_callback, transaction)
        else:
            # FAILURE - Save detailed error info
            return handle_error_callback(result_code, result_desc, checkout_id, transaction)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}, Raw body: {raw_body}")
        return HttpResponseBadRequest(f"Invalid JSON data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": f"Server error: {str(e)}"
        }, status=500)

def handle_success_callback(stk_callback, transaction):
    """Handle successful payment"""
    try:
        metadata_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        
        # Extract data
        metadata = {}
        for item in metadata_items:
            name = item.get("Name")
            value = item.get("Value")
            if name and value is not None:
                metadata[name] = value
        
        amount = metadata.get("Amount")
        mpesa_code = metadata.get("MpesaReceiptNumber")
        phone = metadata.get("PhoneNumber")
        
        logger.info(f"Success: Amount={amount}, Code={mpesa_code}, Phone={phone}")
        
        # Update transaction
        transaction.amount = amount or transaction.amount
        transaction.mpesa_code = mpesa_code
        transaction.phone_number = phone
        transaction.status = "Success"
        transaction.save()
        
        # Update order if exists
        if transaction.order_id:
            update_order_status(transaction.order_id, "paid", mpesa_code)
        
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Payment successful"
        })
        
    except Exception as e:
        logger.error(f"Error in success callback: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": f"Error processing success: {str(e)}"
        })

def handle_error_callback(result_code, result_desc, checkout_id, transaction):
    """Handle failed payment with detailed error info"""
    
    # Map result codes to user-friendly messages
    error_messages = {
        1: "Insufficient balance in your M-PESA account.",
        1032: "You cancelled the payment request.",
        2001: "Incorrect M-PESA PIN entered.",
        1019: "Payment request expired. Please try again.",
        1037: "Unable to reach your phone. Please ensure it's connected.",
        2: "Amount is less than minimum allowed.",
        3: "Amount exceeds maximum allowed.",
        4: "Transaction would exceed daily limit.",
        5: "Transaction would exceed minimum balance.",
        6: "Sender information is invalid.",
        7: "Receiver information is invalid.",
        8: "Transaction would exceed maximum balance.",
        9: "M-PESA system is temporarily unavailable.",
        10: "Transaction timeout.",
        11: "Duplicate transaction.",
        12: "Invalid transaction reference.",
        13: "Invalid amount.",
        14: "Invalid sender.",
        15: "Invalid receiver.",
    }
    
    # Get user-friendly message
    user_message = error_messages.get(result_code, result_desc or "Payment failed.")
    
    # Determine user action
    if result_code in [1]:  # Insufficient balance
        user_action = "check_balance"
    elif result_code in [1032, 2001, 1019, 1037, 10]:  # User errors
        user_action = "retry"
    elif result_code in [2, 3, 4, 5, 8]:  # Limit errors
        user_action = "adjust_amount"
    else:  # System errors
        user_action = "contact_support"
    
    # Update transaction with error details
    transaction.status = "Failed"
    transaction.result_code = result_code
    transaction.result_desc = result_desc
    transaction.user_action = user_action
    
    # Categorize error
    error_category = categorize_error(result_code)
    transaction.error_category = error_category
    
    transaction.save()
    
    logger.warning(f"Payment failed - Code: {result_code}, Desc: {result_desc}, Action: {user_action}")
    
    return JsonResponse({
        "ResultCode": result_code,
        "ResultDesc": result_desc,
        "UserMessage": user_message,
        "UserAction": user_action,
        "ErrorCode": result_code,
        "ErrorCategory": error_category
    })

def categorize_error(result_code):
    """Categorize the error for better handling"""
    user_errors = [1032, 2001]  # Cancelled, wrong PIN
    balance_errors = [1]
    limit_errors = [2, 3, 4, 5, 8]
    timeout_errors = [10, 1019, 1037]
    system_errors = [6, 7, 9, 11, 12, 13, 14, 15]
    
    if result_code in user_errors:
        return "user_error"
    elif result_code in balance_errors:
        return "balance_error"
    elif result_code in limit_errors:
        return "limit_error"
    elif result_code in timeout_errors:
        return "timeout_error"
    elif result_code in system_errors:
        return "system_error"
    else:
        return "unknown_error"

def update_order_status(order_id, status, transaction_code=None):
    """Update order after payment"""
    try:
        
        
        order = CartOrder.objects.get(oid=order_id)
        order.payment_status = status
        if transaction_code:
            order.mpesa_receipt = transaction_code
        order.save()
        logger.info(f"Order {order_id} updated to {status}")
        
    except Exception as e:
        logger.error(f"Failed to update order {order_id}: {str(e)}")