from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from paymentsApp.models import Transactions


@csrf_exempt
def check_payment_status(request):
    if request.method == "GET":
        order_id = request.GET.get("order_id")

        if not order_id:
            return JsonResponse({"status": "error", "message": "No order_id provided"}, status=400)
        transaction = Transactions.objects.filter(order_id=order_id).first()
        if not transaction:
            return JsonResponse({"status": "error", "message": "Transaction not found"}, status=404)

        return JsonResponse({
            "status": "success" if transaction.transaction_status == "paid" else "pending",
            "order_id": transaction.order_id,
            "transaction_status": "paid",
            "amount": transaction.amount,
        }, status=200)



