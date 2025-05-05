import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import logging

# Set up logging - only log to file, not console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="youtube_scraper.log",
    filemode="a",
)
logger = logging.getLogger(__name__)


def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=vi-VN")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def clean_count(count_text):
    if not count_text or count_text == "N/A":
        return count_text
    cleaned = re.sub(r"[^\d.,KMB]", "", count_text)
    return cleaned


def extract_video_info(driver: webdriver.Chrome, url: str) -> dict:
    driver.get(url)

    video_info = {
        "title": "N/A",
        "channel": "N/A",
        "view": "N/A",
        "comments": "N/A",
        "likes": "N/A",
        "publish_date": "N/A",
        "url": url,
    }

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "ytd-watch-flexy"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Title
        try:
            title_tag = soup.select_one(
                "h1.ytd-video-primary-info-renderer yt-formatted-string"
            )
            if title_tag:
                video_info["title"] = title_tag.text.strip()
        except Exception as e:
            logger.warning(f"Error extracting title: {e}")

        # Channel
        try:
            channel_tag = soup.select_one("ytd-channel-name a")
            if channel_tag:
                video_info["channel"] = channel_tag.text.strip()
        except Exception as e:
            logger.warning(f"Error extracting channel: {e}")

        # View count
        try:
            view_tag = soup.select_one(
                "ytd-video-view-count-renderer span.ytd-video-view-count-renderer"
            )
            if view_tag:
                video_info["view"] = clean_count(view_tag.text.strip())
        except Exception as e:
            logger.warning(f"Error extracting view count: {e}")

        # Likes
        try:
            likes_tag = soup.select_one(
                "ytd-toggle-button-renderer yt-formatted-string"
            )
            if likes_tag:
                video_info["likes"] = clean_count(likes_tag.text.strip())
        except Exception as e:
            logger.warning(f"Error extracting likes: {e}")

        # Publish date
        try:
            date_tag = soup.select_one(
                "ytd-video-primary-info-renderer #info-strings yt-formatted-string"
            )
            if date_tag:
                video_info["publish_date"] = date_tag.text.strip()
        except Exception as e:
            logger.warning(f"Error extracting publish date: {e}")

        try:
            driver.execute_script(
                "document.getElementById('comments').scrollIntoView();"
            )
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ytd-comments-header-renderer #count")
                )
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            comment_count_span = soup.select_one("h2#count span")
            if comment_count_span:
                video_info["comments"] = clean_count(comment_count_span.text.strip())
        except TimeoutException:
            logger.warning("Timeout waiting for comments to load")
        except Exception as e:
            logger.warning(f"Error extracting comments: {e}")

    except Exception as e:
        logger.error(f"Error processing video: {e}")

    return video_info


def save_to_csv(video_info: dict, output_path: str):
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "title",
            "channel",
            "view",
            "likes",
            "comments",
            "publish_date",
            "url",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(video_info)


def scrape_single_video(url: str, output_csv: str):
    driver = None
    try:
        driver = setup_driver()
        info = extract_video_info(driver, url)
        save_to_csv(info, output_csv)
        print(f"Đã lưu dữ liệu vào '{output_csv}'")
    except Exception as e:
        logger.error(f"Có lỗi batch scraping: {e}")
    finally:
        if driver:
            driver.quit()


def scrape_multiple_videos(urls: list, output_csv: str):
    all_video_info = []
    driver = None

    try:
        driver = setup_driver()

        for url in urls:
            try:
                info = extract_video_info(driver, url)
                all_video_info.append(info)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")

        with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "title",
                "channel",
                "view",
                "likes",
                "comments",
                "publish_date",
                "url",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for info in all_video_info:
                writer.writerow(info)

        print(f"Đã lưu dữ liệu vào '{output_csv}'")

    except Exception as e:
        logger.error(f"Có lỗi batch scraping: {e}")
    finally:
        if driver:
            driver.quit()
