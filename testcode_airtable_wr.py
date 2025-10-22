import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = "Table 1"

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "fields": {
        "uuid": "테스트-UUID",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": "127.0.0.1",
        "seller_name": "테스트판매처",
        "keywords": "테스트키워드1, 테스트키워드2",
        "results_json": '{"테스트키워드1": "1위", "테스트키워드2": "3위"}'
    }
}

res = requests.post(url, headers=headers, json=data)
print("상태코드:", res.status_code)
print("응답:", res.json())
