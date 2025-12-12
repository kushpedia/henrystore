import requests, base64, json, re, os
from datetime import datetime
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Transaction


from ecomm import settings
# Load environment variables

@csrf_exempt
def payment_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests are allowed")

    try:
        callback_data = json.loads(request.body)
        result_code = callback_data["Body"]["stkCallback"]["ResultCode"]
        checkout_id = callback_data["Body"]["stkCallback"]["CheckoutRequestID"]

        # Find the transaction
        try:
            transaction = Transaction.objects.get(checkout_id=checkout_id)
        except Transaction.DoesNotExist:
            # Create new transaction if not found
            transaction = None

        if result_code == 0:
            # Successful transaction
            metadata = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]

            amount = next(item["Value"] for item in metadata if item["Name"] == "Amount")
            mpesa_code = next(item["Value"] for item in metadata if item["Name"] == "MpesaReceiptNumber")
            phone = next(item["Value"] for item in metadata if item["Name"] == "PhoneNumber")

            if transaction:
                # Update existing transaction
                transaction.amount = amount
                transaction.mpesa_code = mpesa_code
                transaction.phone_number = phone
                transaction.status = "Success"
                transaction.save()
            else:
                # Create new transaction
                Transaction.objects.create(
                    amount=amount,
                    checkout_id=checkout_id,
                    mpesa_code=mpesa_code,
                    phone_number=phone,
                    status="Success"
                )
            
            # Here you should also update your Order model status
            # Example: mark order as paid
            # order = Order.objects.get(...)
            # order.payment_status = 'paid'
            # order.save()
            
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Payment successful"})

        else:
            # Payment failed
            if transaction:
                transaction.status = "Failed"
                transaction.save()
            
            error_message = callback_data["Body"]["stkCallback"].get("ResultDesc", "Payment failed")
            return JsonResponse({
                "ResultCode": result_code, 
                "ResultDesc": error_message
            })

    except (json.JSONDecodeError, KeyError) as e:
        return HttpResponseBadRequest(f"Invalid request data: {str(e)}")