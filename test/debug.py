import json
import requests
import time
summary_api_url = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"
summary_api_key_id = "g8a3pyo6jx"
summary_api_key = "kxiCZbPNZSh62zEGD8cYKIyKtE1a0xtmhMLJtylA"

summary_headers = {
    "X-NCP-APIGW-API-KEY-ID": summary_api_key_id,
    "X-NCP-APIGW-API-KEY": summary_api_key,
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

test_articles = [
    {
        "title": "1000대 기업 매출 15%↑ 2천조 육박…""삼성전자, 21년 연속 1위""",
        "content": "삼성전자(005930)는 지난해 별도 및 연결기준 매출이 각각 200조원, 300조원을 처음으로 돌파해 21년 연속 국내 매출 1위 기업 자리를 지켰다. 기업분석전문 한국CXO연구소는 이 같은 내용의 '1996년~2022년 사이 27년간 국내 1000대 상장사 매출 현황 분석 결과'를 1일 발표했다. 조사..."
    }
]

for index, article in enumerate(test_articles):
    title_clean = article["title"]
    description_clean = article["content"]

    print(f"Processing test article {index + 1}")

    summary_data = {
        "document": {
            "title": title_clean,
            "content": description_clean
        },
        "option": {
            "language": "ko",
            "model": "news",
            "tone": 2,
            "summaryCount": 1
        }
    }
    try:
        print(f"Summarizing test article {index + 1}")
        summary_response = api_post_with_retry(summary_api_url, summary_headers, summary_data)
        if summary_response.status_code == 200:
            summary_result = summary_response.json()
            summary_title = summary_result.get("summary", title_clean)
            print(f"Summary for test article {index + 1}: {summary_title}")
        else:
            summary_title = title_clean
            print(f"Summary API response error for test article {index + 1}")
    except Exception as e:
        print(f"Skipping test article {index + 1} due to summary API error: {e}")
