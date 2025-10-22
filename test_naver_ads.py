"""
네이버 광고 API 테스트 스크립트
정확한 엔드포인트와 파라미터 확인용
"""

import requests
import hmac
import hashlib
import base64
import time
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def test_naver_ads_api():
    """네이버 광고 API 직접 테스트"""
    
    # API 키 로드
    ad_access_license = os.getenv('NAVER_AD_ACCESS_LICENSE')
    ad_secret_key = os.getenv('NAVER_AD_SECRET_KEY')
    customer_id = os.getenv('NAVER_AD_CUSTOMER_ID')
    
    print(f"Access License: {ad_access_license[:20]}...")
    print(f"Secret Key: {ad_secret_key[:20]}...")
    print(f"Customer ID: {customer_id}")
    
    keyword = "키보드"
    
    # 다양한 엔드포인트 시도
    endpoints = [
        "/keywordstool",
        "/ncc/keywords",
        "/tools/keyword",
        "/v1/keywordstool",
        "/ncc/keywordstool"
    ]
    
    for uri in endpoints:
        print(f"\n=== 테스트 중: {uri} ===")
        
        try:
            # 타임스탬프 생성
            timestamp = str(int(time.time() * 1000))
            method = "GET"
            
            # 쿼리 파라미터
            params = f"hintKeywords={keyword}&showDetail=1"
            
            # 서명 메시지
            message = f"{timestamp}.{method}.{uri}?{params}"
            print(f"서명 메시지: {message}")
            
            # HMAC 서명 생성
            secret_key_bytes = base64.b64decode(ad_secret_key)
            signature = hmac.new(
                secret_key_bytes,
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            # 헤더
            headers = {
                'X-Timestamp': timestamp,
                'X-API-KEY': ad_access_license,
                'X-Customer': customer_id,
                'X-Signature': signature_b64,
                'Content-Type': 'application/json'
            }
            
            # API 호출
            url = f"https://api.naver.com{uri}?{params}"
            print(f"URL: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"응답 코드: {response.status_code}")
            print(f"응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 성공! 응답: {data}")
                break
            else:
                try:
                    error_data = response.json()
                    print(f"❌ 오류: {error_data}")
                except:
                    print(f"❌ 오류: {response.text}")
                    
        except Exception as e:
            print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    test_naver_ads_api()