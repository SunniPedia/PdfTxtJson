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

# লগ ফাংশন - স্ক্রিনেও দেখাবে, ফাইলেও লিখবে
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
        log(f"❌ ERROR: {filepath} ফাইল পাওয়া যায়নি!")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    ids = re.split(r'[,\n|\s]+', content)
    clean_ids = [int(i.strip()) for i in ids if i.strip().isdigit()]
    clean_ids = list(dict.fromkeys(clean_ids))
    return clean_ids

# পুরনো লগ ডিলিট করে নতুন শুরু
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log(f"=== Scraping Started ===")
log(f"Input file: {INPUT_FILE}")

PAMPHLET_IDS = load_ids_from_file(INPUT_FILE)
log(f"Found {len(PAMPHLET_IDS)} IDs: {PAMPHLET_IDS}")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

if not PAMPHLET_IDS:
    log("❌ কোনো আইডি পাওয়া যায়নি, শেষ করা হলো।")
    exit(0)

success_count = 0
fail_count = 0

for pamphlet_id in PAMPHLET_IDS:
    log(f"\n--------------------------------------------------")
    log(f"▶️ Processing ID: {pamphlet_id}")
    full_book_text = ""
    book_title = f"pamphlet_{pamphlet_id}"
    page_num = 1
    total_chars = 0

    while True:
        url = BASE_URL.format(pamphlet_id, page_num)
        log(f" -> Fetching Page {page_num}: {url}")
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code!= 200:
                log(f" ⚠️ Page {page_num} not found (Status {res.status_code}), stopping this book.")
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            if page_num == 1:
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    raw_title = title_tag.get_text()
                    raw_title = raw_title.split('-')[0] if 'DawateIslami' in raw_title else raw_title
                    book_title = clean_folder_name(final_clean(raw_title))
                    if not book_title:
                        book_title = f"pamphlet_{pamphlet_id}"
                log(f" 📖 Title Found: {book_title}")

            content_div = (
                soup.find('div', class_='book-content') or
                soup.find('div', class_='page-content') or
                soup.find('article') or
                soup.find('div', id='content')
            )
            page_text = content_div.get_text(separator=' ', strip=True) if content_div else ' '.join([p.get_text() for p in soup.find_all('p')])
            page_text = final_clean(page_text)

            if len(page_text) < 50:
                log(f" ⏹️ Page {page_num} empty (<50 chars), ending.")
                break

            full_book_text += page_text + "\n\n"
            total_chars += len(page_text)
            log(f" ✅ Page {page_num} done - {len(page_text)} chars")
            page_num += 1
            time.sleep(1)

        except Exception as e:
            log(f" ❌ Error on ID {pamphlet_id} Page {page_num}: {e}")
            break

    if full_book_text:
        safe_file_name = clean_folder_name(book_title) + ".txt"
        file_path = os.path.join(OUTPUT_FOLDER, safe_file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{book_title}\nID: {pamphlet_id}\nSource: https://www.dawateislami.net/pamphlets/{pamphlet_id}\n{'='*40}\n\n{full_book_text}")
        log(f"💾 SAVED: {file_path} | Total Pages: {page_num-1} | Total Chars: {total_chars}")
        success_count += 1
    else:
        log(f"❌ FAILED: No content for ID {pamphlet_id}")
        fail_count += 1

log(f"\n==================================================")
log(f"=== Scraping Finished ===")
log(f"✅ Success: {success_count} | ❌ Failed: {fail_count} | Total: {len(PAMPHLET_IDS)}")
log(f"==================================================")
