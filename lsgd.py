import requests
import uuid
import time
import json
import re

def getcookie():
    with open('cookies.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def get_device_id():
    return str(uuid.uuid4()).upper()

def get_zalopay_id():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Cookie": getcookie()
    }
    reponse = requests.get("https://sapi.zalopay.vn/v2/user/profile/kyc", headers=headers)
    return reponse.json()["data"]["zalopay_id"]

def get_access_token():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Cookie": getcookie()
    }
    response = requests.get("https://sapi.zalopay.vn/v2/zalo/access-token", headers=headers)
    return response.json()["data"]["zalo_access_token"]


def get_history():
    headers = {
        "User-Agent": "Mozilla/5.0 (Android 8.1.0; Mobile; rv:123.0) Gecko/123.0 Firefox/123.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Cookie": getcookie()
    }

    try:
        response_noti = requests.get("https://api.zalopay.vn/v1/notification/messages?size=200", headers=headers)
        if response_noti.status_code != 200:
            return {"data": {"status": "false", "message": "Cookie die hoặc lỗi kết nối"}}

        noti_data = response_noti.json()
        msg_items = noti_data.get('data', {}).get('msg_items', [])
        
        history_list = []

        for item in msg_items:
            if len(history_list) >= 20: 
                break

            try:
                inner = json.loads(item.get('data', '{}'))
                
                title = inner.get('embeddata', {}).get('boldtitle', '')
                if not title:
                    title = inner.get('boldtitle', '')

                if "Nhận tiền" not in title:
                    continue

                zpa_data = inner.get('notification_action', {}).get('zpa', {}).get('data', '')
                zpi_data = inner.get('notification_action', {}).get('zpi', {}).get('data', '')
                
                match = re.search(r'trans_id=(\d+)', zpa_data) or re.search(r'history/(\d+)', zpi_data)
                if not match:
                    continue
                
                trans_id = match.group(1)

                detail_url = f"https://sapi.zalopay.vn/v2/history/transactions/{trans_id}?type=1"
                res_detail = requests.get(detail_url, headers=headers)
                
                if res_detail.status_code == 200:
                    d = res_detail.json().get('data', {}).get('transaction', {})
                    fields = d.get('template_info', {}).get('custom_fields', [])
                    
                    # Tìm nội dung lời nhắn từ danh sách custom_fields
                    description_value = d.get('description', '')  # Mặc định nếu không tìm thấy lời nhắn
                    for field in fields:
                        if field.get('name') == 'Lời nhắn':
                            description_value = field.get('value', '').strip()
                            break  # Tìm thấy rồi thì dừng vòng lặp luôn
                    
                    history_list.append({
                        "trans_id": str(d.get('trans_id', trans_id)),
                        "trans_time": d.get('trans_time'),
                        "title": title,
                        "description": description_value,
                        "amount": d.get('trans_amount', 0),
                        "balance": d.get('balance_snapshot', 0)
                    })

            except Exception as e:
                print(f"Bỏ qua 1 item lỗi: {e}")
                continue

        return {
            "data": {
                "status": "true",
                "message": "Thành Công!",
                "history": history_list
            }
        }

    except Exception as e:
        return {"data": {"status": "false", "message": str(e)}}

print(get_history())
