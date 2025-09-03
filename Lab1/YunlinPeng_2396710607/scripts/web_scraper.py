import os
import sys
import re
from pathlib import Path
from urllib.parse import urljoin
import html as html_lib
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAVE_WDM = True
except Exception:
    HAVE_WDM = False

URL = "https://www.cnbc.com/world/?region=world"
UA  = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"

def chromium_options() -> Options:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    
    for p in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"):
        if os.path.exists(p):
            opts.binary_location = p
            break
    opts.add_argument(f"user-agent={UA}")
    return opts

def start_driver() -> webdriver.Chrome:
   
    opts = chromium_options()

    snap_driver = "/snap/bin/chromium.chromedriver"
    if os.path.exists(snap_driver) and os.access(snap_driver, os.X_OK):
        try:
            service = ChromeService(executable_path=snap_driver)
            return webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            print(f"Failed: {e}", file=sys.stderr)

    try:
        return webdriver.Chrome(options=opts)
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)

    if HAVE_WDM:
        try:
            wdm_cache = Path.home() / ".wdm" / "drivers" / "chromedriver"
            if wdm_cache.exists():
                import shutil
                shutil.rmtree(wdm_cache, ignore_errors=True)
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            print(f"Failed: {e}", file=sys.stderr)

    raise RuntimeError("Could not start Chromium driver.")

def get_dynamic_blocks():
    driver = start_driver()
    wait = WebDriverWait(driver, 30)
    markets_html = latest_html = ""

    try:
        driver.get(URL)
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            btn.click()
        except Exception:
            pass 
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        def get_markets_outer_html():
            try:
                el = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "market-data-scroll-container")))
                return el.get_attribute("outerHTML")
            except Exception:
                pass

            try:
                el = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".MarketsBanner-marketData")))
                return el.get_attribute("outerHTML")
            except Exception:
                pass
        
            html = driver.execute_script("""
                const el = document.querySelector('#market-data-scroll-container, .MarketsBanner-marketData');
                return el ? el.outerHTML : null;
            """)
            return html or ""

        driver.execute_script("window.scrollTo(0, 0);")
        markets_html = get_markets_outer_html()
        if not markets_html:
            driver.execute_script("window.scrollBy(0, 500);")
            markets_html = get_markets_outer_html()

        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.LatestNews-list")))
            latest_html = el.get_attribute("outerHTML")
        except Exception:
            latest_html = driver.execute_script("""
                const el = document.querySelector('ul.LatestNews-list');
                return el ? el.outerHTML : "";
            """) or ""

    finally:
        try:
            driver.quit()
        except PermissionError as e:
            print(file=sys.stderr)

    def fix_links(s: str) -> str:
        return s.replace('href="//', 'href="https://') if s else s

    return fix_links(markets_html), fix_links(latest_html)


def get_latest_news():
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    ul = soup.select_one("ul.LatestNews-list") or soup.find("ul", class_=re.compile("LatestNews-list"))
    items = []
    if ul:
        for li in ul.select("li.LatestNews-item"):
            a = li.select_one("a.LatestNews-headline")
            if not a:
                continue
            time = li.select_one("time.LatestNews-timestamp")
            href = a.get("href") or ""
            if href.startswith("//"):
                href = "https:" + href
            else:
                href = urljoin(URL, href)
            items.append((
                (time.get_text(strip=True) if time else ""),
                a.get_text(strip=True),
                href
            ))
    return items

def main():
    markets_html, latest_html = get_dynamic_blocks()
    latest_list = get_latest_news()

    htmls = []
    if markets_html:
        htmls.append(markets_html)
    if latest_html:
        htmls.append(latest_html)
    if latest_list:
        htmls.append("<ul>")
        for tm, title, href in latest_list:
            htmls.append(
                f"<li>{html_lib.escape(tm)} — "
                f"<a href='{html_lib.escape(href)}'>{html_lib.escape(title)}</a></li>"
            )
        htmls.append("</ul>")

    save_folder = Path("/home/linda/Desktop/YunlinPeng_2396710607/data/raw_data")
    output = save_folder / "web_data.html"
    output.write_text("\n".join(htmls), encoding="utf-8")

    with output.open(encoding="utf-8") as f:
        for i in range(10):
            line = f.readline()
            if not line:
                break
            print(line.rstrip())

if __name__ == "__main__":
    main()
