from pathlib import Path
from bs4 import BeautifulSoup
import csv

html_file = Path("/home/linda/Desktop/YunlinPeng_2396710607/data/raw_data/web_data.html")
with html_file.open(encoding="utf-8") as f:
    html_lines = [line.rstrip("\n") for line in f]

html_text = "\n".join(html_lines)
soup = BeautifulSoup(html_text, "lxml")

markets = []
print("Filtering market fields")
for card in soup.select("#market-data-scroll-container a.MarketCard-container"):
    symbol = card.select_one(".MarketCard-symbol")
    stock_pos = card.select_one(".MarketCard-stockPosition")
    change_pct = card.select_one(".MarketCard-changesPct")
    if symbol and stock_pos and change_pct:
        markets.append({
            "symbol": symbol.get_text(strip=True),
            "stock_pos": stock_pos.get_text(strip=True),
            "change_pct": change_pct.get_text(strip=True),
        })

print("Storing Market data")
markets_csv = Path("/home/linda/Desktop/YunlinPeng_2396710607/data/processed_data/market_data.csv")
with markets_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["symbol", "stock_pos", "change_pct"])
    writer.writeheader()
    writer.writerows(markets)
print("Market CSV Created")

latest_news = []
print("Filtering latest news fields")
for li in soup.select("ul.LatestNews-list li.LatestNews-item"):
    ts = li.select_one(".LatestNews-timestamp")
    a = li.select_one("a.LatestNews-headline")
    if a:
        latest_news.append({
            "timestamp": ts.get_text(strip=True) if ts else "",
            "title": a.get_text(strip=True),
            "link": a.get("href"),
        })

print("Storing latest news data")
latest_news_csv = Path("/home/linda/Desktop/YunlinPeng_2396710607/data/processed_data/news_data.csv")
with latest_news_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "title", "link"])
    writer.writeheader()
    writer.writerows(latest_news)
print("Latest news CSV Created")
