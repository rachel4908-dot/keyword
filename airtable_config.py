# airtable_config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Airtable Personal Access Token
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "patZsvg3EZpC3PzWm.ff0ffa750a9d44ec7a05f95d905ca97e9b36d11b8059c690f9aead0a91aead82")

# Airtable Base ID (예: 사용자 등록용 Base)
BASE_ID = os.getenv("BASE_ID", "appMugT8Jwsv6lnhd")

# (선택) 테이블 이름 상수화
USERS_TABLE_NAME = "Users"
SEARCH_LOGS_TABLE_NAME = "SearchLogs"
CONTROL_TABLE_NAME = "Control"
