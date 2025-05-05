from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict


def setup_driver() -> webdriver.Chrome:
    """Khởi tạo trình duyệt headless."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def scroll_to_bottom(driver: webdriver.Chrome, delay: float = 3.0) -> None:
    """Cuộn trang cho đến khi không còn nội dung mới."""
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        driver.execute_script(
            "window.scrollTo(0, document.documentElement.scrollHeight);"
        )
        time.sleep(delay)
        new_height = driver.execute_script(
            "return document.documentElement.scrollHeight"
        )
        if new_height == last_height:
            break
        last_height = new_height


def extract_video_data(soup: BeautifulSoup, limit: int = None) -> List[Dict]:
    """Trích xuất thông tin video từ HTML."""
    video_elements = soup.select("ytd-playlist-video-renderer")
    results = []

    for video in video_elements[:limit] if limit else video_elements:
        try:
            title_tag = video.select_one("a#video-title")
            title = title_tag.get("title").strip() if title_tag else "N/A"
            href = title_tag.get("href").strip() if title_tag else ""
            video_url = f"https://www.youtube.com{href}" if href else "N/A"

            channel_tag = video.select_one("#byline-container ytd-channel-name a")
            channel = channel_tag.text.strip() if channel_tag else "N/A"

            view_tag = video.select_one("#byline-container #video-info span")
            view = view_tag.text.strip() if view_tag else "N/A"

            results.append(
                {"title": title, "channel": channel, "view": view, "url": video_url}
            )
        except Exception as e:
            print("Lỗi khi xử lý video:", e)

    return results


def save_to_csv(data: List[Dict], output_file: str) -> None:
    """Lưu danh sách dữ liệu vào file CSV."""
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"Đã lưu {len(df)} video vào '{output_file}'.")


def scrape_youtube_playlist(
    url: str, num_of_video: int = None, output_csv: str = "data.csv"
) -> None:
    """Hàm tổng điều phối quá trình scrape YouTube playlist."""
    driver = setup_driver()

    driver.get(url)
    time.sleep(3)

    scroll_to_bottom(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    data = extract_video_data(soup, limit=num_of_video)

    save_to_csv(data, output_csv)

    driver.quit()
