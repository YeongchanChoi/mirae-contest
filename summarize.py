import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

summary_api_url = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"
summary_api_key_id = "g8a3pyo6jx"
summary_api_key = "kxiCZbPNZSh62zEGD8cYKIyKtE1a0xtmhMLJtylA"

# 요청 헤더
summary_headers = {
    "X-NCP-APIGW-API-KEY-ID": summary_api_key_id,
    "X-NCP-APIGW-API-KEY": summary_api_key,
    "Content-Type": "application/json"
}

def api_post_with_retry(url, headers, data, retries=3):
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            return response
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

def process_article(row, stock_name):
    pubDate = row['날짜']
    pubDate_parsed = datetime.strptime(pubDate, '%Y.%m.%d.')
    pubDate_str = pubDate_parsed.strftime('%Y.%m.%d')
    title_clean = row['제목']
    description_clean = row['내용']

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
        summary_response = api_post_with_retry(summary_api_url, summary_headers, summary_data)
        if summary_response.status_code == 200:
            summary_result = summary_response.json()
            summary_title = summary_result.get("summary", title_clean)
        else:
            summary_title = title_clean
    except Exception as e:
        print(f"Skipping article due to summary API error: {e}")
        summary_title = title_clean

    return (pubDate_str, stock_name, summary_title)

with open('종목.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    stock_names = [row[0] for row in reader]

start_date = datetime.strptime("2023-06-01", "%Y-%m-%d")
end_date = datetime.strptime("2024-06-01", "%Y-%m-%d")
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
date_range_str = [date.strftime("%Y.%m.%d") for date in date_range]

for stock_name in stock_names:
    print(f"Processing stock: {stock_name}")
    
    summary_folder = os.path.join("summarize", stock_name)
    os.makedirs(summary_folder, exist_ok=True)
    summary_file_path = os.path.join(summary_folder, "summary_data.csv")

    folder_path = os.path.join("crawling", stock_name)
    file_path = os.path.join(folder_path, "news_data.csv")

    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        with open(summary_file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['날짜', '기업이름', '요약내용'])

            with ThreadPoolExecutor(max_workers=1000) as executor:
                future_to_article = {executor.submit(process_article, row, stock_name): row for index, row in df.iterrows()}
                for future in as_completed(future_to_article):
                    try:
                        result = future.result()
                        writer.writerow(result)
                    except Exception as e:
                        print(f"Error processing article: {e}")

print("Summary process completed.")
