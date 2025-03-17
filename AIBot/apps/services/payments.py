import hashlib
import os
import uuid

def generate_payment_link(user_id, amount):
    order_id = str(uuid.uuid4().hex[:16])
    amount = str(amount)
    currency = "RUB"
    sign_str = f"{os.getenv('MERCHANT_ID')}:{amount}:{os.getenv('FREEKASSA_SECRET_KEY')}:{currency}:{order_id}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()

    payment_url = (f"https://pay.freekassa.ru/?m={os.getenv('MERCHANT_ID')}"
                   f"&oa={amount}&currency={currency}&o={order_id}&s={sign}&em=123")
    return order_id, payment_url



