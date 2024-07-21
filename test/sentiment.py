import os
import json
import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import time
import csv

sentiment_api_url = "https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze"
sentiment_api_key_id = "g8a3pyo6jx"
sentiment_api_key = "kxiCZbPNZSh62zEGD8cYKIyKtE1a0xtmhMLJtylA"

# 요청 헤더
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

def analyze_sentiment(summary_title):
    sentiment_data = {
        "content": summary_title
    }
    sentiment_response = api_post_with_retry(sentiment_api_url, sentiment_headers, sentiment_data)
    if sentiment_response.status_code == 200:
        sentiment_result = sentiment_response.json()
        confidence_positive = sentiment_result["document"]["confidence"]["positive"]
        confidence_negative = sentiment_result["document"]["confidence"]["negative"]
        confidence_sum = confidence_positive - confidence_negative
        return confidence_sum
    else:
        print(f"Error in sentiment response: {sentiment_response.text}")
        return 0

def process_stock_summary(stock_name, date_range_str):
    sentiment_dict = {date: [] for date in date_range_str}
    summary_folder_path = os.path.join("summarize", stock_name)
    summary_file_path = os.path.join(summary_folder_path, "summary_data.csv")

    if os.path.exists(summary_file_path):
        df = pd.read_csv(summary_file_path, encoding='utf-8-sig')

        for index, row in df.iterrows():
            pubDate_str = row['날짜']
            summary_title = row['요약내용']

            print(f"Analyzing sentiment for summary {index + 1} on date {pubDate_str}")
            confidence_sum = analyze_sentiment(summary_title)
            sentiment_dict[pubDate_str].append(confidence_sum)
            print(f"Sentiment confidence (positive - negative): {confidence_sum}")

    return sentiment_dict

def calculate_sentiment_summary(stock_name, date_range_str, sentiment_dict):
    sentiment_summary_list = []
    for date in date_range_str:
        if sentiment_dict[date]:
            mean_sentiment = np.mean(sentiment_dict[date])
            var_sentiment = np.var(sentiment_dict[date])
        else:
            mean_sentiment = 0
            var_sentiment = 0
        sentiment_summary_list.append((stock_name, date, mean_sentiment, var_sentiment))
        print(f"Date: {date}, Mean sentiment: {mean_sentiment}, Variance: {var_sentiment}")

    return sentiment_summary_list

def main():
    with open('종목.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        stock_names = [row[0] for row in reader]

    start_date = datetime.strptime("2023-06-01", "%Y-%m-%d")
    end_date = datetime.strptime("2024-06-01", "%Y-%m-%d")
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
    date_range_str = [date.strftime("%Y.%m.%d") for date in date_range]

    # 데이터베이스 연결
    conn = sqlite3.connect('sentiment_analysis.db')
    c = conn.cursor()

    # 테이블 생성
    c.execute('''
    CREATE TABLE IF NOT EXISTS SentimentSummary (
        종목명 TEXT,
        날짜 TEXT,
        평균값 REAL,
        분산값 REAL
    )
    ''')

    for stock_name in stock_names:
        print(f"Processing stock: {stock_name}")
        sentiment_dict = process_stock_summary(stock_name, date_range_str)
        sentiment_summary_list = calculate_sentiment_summary(stock_name, date_range_str, sentiment_dict)

        # 데이터베이스에 저장
        c.executemany('''
        INSERT INTO SentimentSummary (종목명, 날짜, 평균값, 분산값) VALUES (?, ?, ?, ?)
        ''', sentiment_summary_list)
        conn.commit()

    print(f"Sentiment analysis process completed.")
    conn.close()

if __name__ == "__main__":
    main()
