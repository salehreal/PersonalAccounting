import requests

def send_sms(recipients, code):
    try:
        response = requests.post(
            url="https://api2.ippanel.com/api/v1/sms/pattern/normal/send",
            headers={
                'apikey': 'OWY0YjhmMWUtZGFlOS00MTViLWI5MmItMDMyMmZhMWRkMjg4ZmM5ZGE0ZTRkNWNlOTRhNjBhZjBhNTlmOWQ5NDcwOTE=',
                'Content-Type': 'application/json'
            },
            json={
                "code": "fqmt1275wjd02wg",
                "sender": "+983000505",
                "recipient": recipients,
                "variable": {
                    "verification-code": code
                }
            }
        )

        if response.status_code == 200:
            return True
        else:
            print("SMS failed:", response.status_code, response.text)
            return False

    except Exception as e:
        print("SMS Exception:", e)
        return False
