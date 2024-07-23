import os
import time
import re
import csv
import urllib.parse
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

with open('종목.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader) 
    stock_names = [row[0] for row in reader]

options = Options()
options.add_argument("--headless") 
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def remove_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# 날짜 범위
start_date = datetime.strptime("2023-06-01", "%Y-%m-%d")
end_date = datetime.strptime("2024-06-01", "%Y-%m-%d")
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]

for stock_name in stock_names:
    print(f"Processing stock: {stock_name}")
    all_articles = []

    for date in date_range:
        formatted_date = date.strftime("%Y.%m.%d")
        next_date = (date).strftime("%Y.%m.%d")
        url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(stock_name)}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={formatted_date}&de={next_date}&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Ar%2Cp%3Afrom{formatted_date.replace('.', '')}to{next_date.replace('.', '')}&is_sug_officeid=0&office_category=0&service_area=0"
        
        driver.get(url)

        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.group_news > ul.list_news')))
        except:
            print(f"No articles found for date {formatted_date}")
            continue
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = []
        ul = soup.select_one('div.group_news > ul.list_news')

        if ul:
            li_tags = ul.select('li.bx')

            for li in li_tags[:20]:  # 뉴스 개수 20
                date_text = li.select_one('div.news_area div.info_group span.info').get_text()
                if re.match(r'^\d{4}\.\d{2}\.\d{2}\.$', date_text):
                    title = li.select_one('div.news_area a.news_tit').get_text()
                    content = li.select_one('div.news_area div.dsc_wrap a.api_txt_lines').get_text()
                    articles.append([date_text, title, content])

        if articles:
            all_articles.extend(articles)

    if all_articles:
        df = pd.DataFrame(all_articles, columns=["날짜", "제목", "내용"])
        folder_path = os.path.join("crawling", stock_name)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "news_data.csv")
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

driver.quit()
print("Web driver closed.")
