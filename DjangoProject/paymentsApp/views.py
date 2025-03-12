from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

import hashlib
import os
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

from paymentsApp.models import *

load_dotenv()

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        data = request.POST

        order_id = data.get('MERCHANT_ORDER_ID')
        amount = data.get('AMOUNT')
        sign = data.get('SIGN')

        merchant_id = os.getenv('MERCHANT_ID')
        secret_key_2 = os.getenv('SECRET_KEY_2')

        sign_check = hashlib.md5(f'{merchant_id}:{amount}:{secret_key_2}:{order_id}'.encode()).hexdigest()

        if sign != sign_check:
            return JsonResponse({"status": "error", "message": "Invalid signature"}, status=400)

        try:
            transaction = Transactions.objects.filter(order_id=order_id).first()
            if not transaction:
                return JsonResponse({"status": "error", "message": "No transaction"}, status=400)

            if transaction.transaction_status == 'paid':
                return HttpResponse("YES", status=200)

            transaction.transaction_status = 'paid'
            transaction.save()

            return HttpResponse("YES", status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": "Transaction not found"}, status=500)

@csrf_exempt
def payment_success(request):
    return render(request, 'success.html')

@csrf_exempt
def payment_error(request):
    return render(request, 'error.html')
