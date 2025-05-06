import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time


# Hàm thiết lập trình duyệt Chrome
def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")  # Chạy không hiển thị giao diện
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=vi-VN")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


# Hàm làm sạch dữ liệu số (view)
def clean_count(count_text):
    if not count_text or count_text == "N/A":
        return count_text
    cleaned = re.sub(r"[^\d.,KMB]", "", count_text)
    return cleaned


# Hàm trích xuất thông tin từ video
def extract_video_info(driver: webdriver.Chrome, url: str) -> dict:
    driver.get(url)
    video_info = {
        "title": "N/A",
        "channel": "N/A",
        "view": "N/A",
        "url": url,
    }

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "ytd-watch-flexy"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Lấy tiêu đề (title)
        title_tag = soup.select_one(
            "h1.ytd-video-primary-info-renderer yt-formatted-string"
        )
        if title_tag:
            video_info["title"] = title_tag.text.strip()

        # Lấy tên kênh (channel)
        channel_tag = soup.select_one("ytd-channel-name a")
        if channel_tag:
            video_info["channel"] = channel_tag.text.strip()

        # Lấy số lượt xem (view count)
        view_tag = soup.select_one(
            "ytd-video-view-count-renderer span.ytd-video-view-count-renderer"
        )
        if view_tag:
            video_info["view"] = clean_count(view_tag.text.strip())

    except TimeoutException:
        print("Timeout waiting for page to load")
    except Exception as e:
        print(f"Error processing video: {e}")

    return video_info


# Hàm lưu dữ liệu vào file CSV
def save_to_csv(video_info: dict, output_path: str):
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "channel", "view", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(video_info)


# Hàm thu thập dữ liệu từ một video
def scrape_single_video(url: str, output_csv: str = "data.csv"):
    driver = None
    try:
        driver = setup_driver()
        info = extract_video_info(driver, url)
        save_to_csv(info, output_csv)
        print(f"Đã lưu tại '{output_csv}'")
    except Exception as e:
        print(f"Có lỗi khi scraping: {e}")
    finally:
        if driver:
            driver.quit()
