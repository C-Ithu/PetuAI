import json, os, urllib.request, urllib.error
MP_API="https://api.mercadopago.com"
PLAN_AMOUNT=1000
PLAN_CURRENCY="CLP"
def _token():
    token=os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not token: raise RuntimeError("Mercado Pago is not configured")
    return token
def _request(path,method="GET",payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(MP_API+path,data=data,method=method,headers={"Authorization":f"Bearer {_token()}","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as res: return json.loads(res.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Mercado Pago error {exc.code}") from exc
def create_subscription(email:str,back_url:str):
    body={"reason":"PetuAI Plan Mensual","payer_email":email,"auto_recurring":{"frequency":1,"frequency_type":"months","transaction_amount":PLAN_AMOUNT,"currency_id":PLAN_CURRENCY},"back_url":back_url,"status":"pending"}
    data=_request("/preapproval","POST",body)
    return {"subscription_id":data["id"],"checkout_url":data["init_point"],"status":data.get("status","pending")}
def get_subscription(subscription_id:str):
    data=_request("/preapproval/"+subscription_id)
    return {"id":data.get("id"),"status":data.get("status"),"payer_email":data.get("payer_email"),"amount":PLAN_AMOUNT,"currency":PLAN_CURRENCY}
