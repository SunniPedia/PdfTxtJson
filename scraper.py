import os
import time
import requests
from bs4 import BeautifulSoup
import html
import re
from datetime import datetime

INPUT_FILE = "pamphlet.txt"
OUTPUT_FOLDER = "pamphletTXT"
LOG_FILE = "scraping.log"
BASE_URL = "https://www.dawateislami.net/pamphlets/{}/page/{}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def clean_folder_name(name):
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def final_clean(text):
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r'\s+([।,:!])', r'\1', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def load_ids_from_file(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    ids = re.split(r'[,\n|\s]+', content)
    clean_ids = [int(i.strip()) for i in ids if i.strip().isdigit()]
    return list(dict.fromkeys(clean_ids))

# Log start fresh
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log(f"=== Scraping Started ===")
PAMPHLET_IDS = load_ids_from_file(INPUT_FILE)
log(f"Found {len(PAMPHLET_IDS)} IDs from {INPUT_FILE}")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for pamphlet_id in PAMPHLET_IDS:
    log(f"\n--------------------------------------------------")
    log(f"▶️ ID: {pamphlet_id} - https://www.dawateislami.net/pamphlets/{pamphlet_id}")

    full_book_text = ""
    book_title = f"pamphlet_{pamphlet_id}"
    seen_hashes = set()
    total_pages_site = None

    for page_num in range(1, 1000): # Safety limit 1000, কিন্তু আগেই থামবে
        url = BASE_URL.format(pamphlet_id, page_num)
        log(f" -> Page {page_num} fetching...")

        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200:
                log(f" ⏹️ Status {res.status_code}, ending book.")
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            # 1. Total Pages বের করা - সাইটেই দেওয়া আছে
            if page_num == 1:
                # পেজে "Total Pages" লেখাটা থাকে
                total_text = soup.get_text()
                match = re.search(r'Total Pages\s*(\d+)', total_text, re.IGNORECASE)
                if match:
                    total_pages_site = int(match.group(1))
                    log(f" 📄 Site says Total Pages = {total_pages_site}")
                
                title_tag = soup.find('h1')
                if title_tag:
                    book_title = clean_folder_name(final_clean(title_tag.get_text())) or book_title
                log(f" 📖 Title: {book_title}")

            # 2. আসল কন্টেন্ট বের করা
            # আগের ভুল selector বাদ দিয়ে শুধু main text area
            content_area = soup.find('div', class_='book-reader') or soup.find('main') or soup.find('div', {'id': 'book-reader'})
            # Fallback: body থেকে নয়, নির্দিষ্ট div
            if content_area:
                page_text = content_area.get_text(separator=' ', strip=True)
            else:
                # সব p নয়, শুধু যেখানে আরবি/বাংলা বেশি
                page_text = ' '.join([p.get_text(separator=' ') for p in soup.select('div p')][:20])

            page_text = final_clean(page_text)

            # 3. --- ৩টা থামার শর্ত ---
            # ক) কন্টেন্ট খুব ছোট হলে
            if len(page_text) < 80:
                log(f" ⏹️ Page too small ({len(page_text)} chars), ending.")
                break

            # খ) একই কন্টেন্ট বারবার আসলে (তোমার 556 chars সমস্যার ফিক্স)
            text_hash = hash(page_text[:200]) # প্রথম 200 অক্ষর দিয়ে চেক
            if text_hash in seen_hashes:
                log(f" ⏹️ Duplicate content detected, ending. (Loop fixed)")
                break
            seen_hashes.add(text_hash)

            # গ) সাইটের Total Pages পার হয়ে গেলে
            if total_pages_site and page_num > total_pages_site:
                log(f" ⏹️ Reached site Total Pages ({total_pages_site}), ending.")
                break

            full_book_text += f"--- Page {page_num} ---\n" + page_text + "\n\n"
            log(f" ✅ Page {page_num} OK - {len(page_text)} chars")

            # যদি Total Pages জানা থাকে, সেখানেই থামো
            if total_pages_site and page_num >= total_pages_site:
                log(f" ✅ Reached last page {total_pages_site}")
                break

            time.sleep(0.8)

        except Exception as e:
            log(f" ❌ Error: {e}")
            break

    if full_book_text:
        file_path = os.path.join(OUTPUT_FOLDER, clean_folder_name(book_title) + ".txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{book_title}\nID: {pamphlet_id}\n{'='*40}\n\n{full_book_text}")
        log(f"💾 SAVED: {file_path} | Pages: {page_num}")
    else:
        log(f"❌ FAILED: {pamphlet_id}")

log(f"\n=== All Done ===")
