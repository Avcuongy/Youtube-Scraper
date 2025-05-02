from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from bs4 import BeautifulSoup


def scrape_youtube_playlist(
    url: str, num_of_video: int = None, scroll_rounds: int = 30, output_csv="data.csv"
):
    # Set up Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Chạy ẩn
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    # Truy cập playlist
    driver.get(url)
    time.sleep(3)  # Đợi trang tải

    # Cuộn trang
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    for i in range(scroll_rounds):
        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )
        time.sleep(3)
        new_height = driver.execute_script(
            "return document.documentElement.scrollHeight"
        )
        if new_height == last_height:
            break  # Không còn nội dung mới
        last_height = new_height

    # Parse HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Lấy tất cả video
    video_elements = soup.select("ytd-playlist-video-renderer")
    results = []

    for video in video_elements[:num_of_video] if num_of_video else video_elements:
        try:
            # Title
            title_tag = video.select_one("a#video-title")
            title = title_tag.get("title").strip() if title_tag else "N/A"

            # Channel
            channel_tag = video.select_one("#byline-container ytd-channel-name a")
            channel = channel_tag.text.strip() if channel_tag else "N/A"

            # View
            info_tag = video.select_one("#byline-container #video-info span")
            view = info_tag.text.strip() if info_tag else "N/A"

            results.append({"title": title, "channel": channel, "view": view})
        except Exception as e:
            print("Lỗi khi xử lý video:", e)

    # Đóng trình duyệt
    driver.quit()

    # Xuất ra CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Đã lưu {len(df)} video vào {output_csv}")
