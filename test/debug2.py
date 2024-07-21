import json
import requests
import time

sentiment_api_url = "https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze"
sentiment_api_key_id = "g8a3pyo6jx"
sentiment_api_key = "kxiCZbPNZSh62zEGD8cYKIyKtE1a0xtmhMLJtylA"

sentiment_headers = {
    "X-NCP-APIGW-API-KEY-ID": sentiment_api_key_id,
    "X-NCP-APIGW-API-KEY": sentiment_api_key,
    "Content-Type": "application/json"
}

def api_post_with_retry(url, headers, data, retries=3):
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

example_text = "인텔·엔비디아·퀄컴 등과 '라이즈' 프로젝트 운영 이사회 멤버 참여 삼성전자가 첨단  반도체 생태계 구축 및 확산을 위한 오픈소스 소프트웨어(SW) 개발 프로젝트에 참여합니다."

sentiment_data = {
    "content": example_text
}
try:
    print(f"Analyzing sentiment for the example text")
    sentiment_response = api_post_with_retry(sentiment_api_url, sentiment_headers, sentiment_data)
    if sentiment_response.status_code == 200:
        sentiment_result = sentiment_response.json()
        confidence_positive = sentiment_result["document"]["confidence"]["positive"]
        confidence_negative = sentiment_result["document"]["confidence"]["negative"]
        confidence_sum = confidence_positive - confidence_negative
        print(f"Sentiment confidence (positive - negative): {confidence_sum}")
        print(f"Full sentiment analysis result: {sentiment_result}")
    else:
        print("Sentiment analysis failed.")
except Exception as e:
    print(f"Sentiment analysis error: {e}")
