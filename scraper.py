import os
import time
import requests
from bs4 import BeautifulSoup
import html
import re

# তোমার দেওয়া নির্দিষ্ট আইডি গুলো
PAMPHLET_IDS = [
    8092, 8106, 8121, 8133, 8155, 8170, 8185, 8222, 8226, 8240, 8258, 8269, 8285, 8299, 8312, 8328, 8364, 8384, 8398, 8432, 8446, 8466, 8481, 8503, 8514, 8536, 8551, 8565, 8581, 8595, 8614, 8627, 8633, 8666, 8681, 8693, 8715, 8728, 8754, 8769, 8784, 8791, 8838, 8860, 8903, 8913, 8931, 8943, 8962, 8969, 8993, 9010, 9026, 9038, 9055, 9094, 9103, 9118, 9131, 9175, 9191, 9213, 9228, 9239, 9258, 9271, 9298
]

BASE_URL = "https://www.dawateislami.net/pamphlets/{}/page/{}"
OUTPUT_FOLDER = "pamphletTXT"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def clean_folder_name(name):
    # ফোল্ডারের নামে ব্যবহার করা যাবে না এমন ক্যারেক্টারগুলো সরানো
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

# আউটপুট ফোল্ডার তৈরি
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for pamphlet_id in PAMPHLET_IDS:
    print(f"\n--- Processing ID: {pamphlet_id} ---")
    full_book_text = ""
    book_title = f"pamphlet_{pamphlet_id}"
    page_num = 1

    while True:
        url = BASE_URL.format(pamphlet_id, page_num)
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code!= 200:
                print(f" Page {page_num} not found (Status {res.status_code}), stopping.")
                break

            soup = BeautifulSoup(res.text, 'html.parser')

            # 1. কিতাবের নাম বের করা (প্রথম পেজ থেকে)
            if page_num == 1:
                # Title tag বা h1 থেকে নাম বের করার চেষ্টা
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    raw_title = title_tag.get_text()
                    # "Page 1 - Title - DawateIslami" থেকে Title বের করা
                    raw_title = raw_title.split('-')[0] if 'DawateIslami' in raw_title else raw_title
                    book_title = clean_folder_name(final_clean(raw_title))
                    if not book_title:
                        book_title = f"pamphlet_{pamphlet_id}"
                print(f" Title Found: {book_title}")

            # 2. পেজের মূল টেক্সট বের করা - dawateislami এর জন্য কয়েকটি selector ট্রাই
            content_div = (
                soup.find('div', class_='book-content') or
                soup.find('div', class_='page-content') or
                soup.find('article') or
                soup.find('div', id='content')
            )

            if content_div:
                page_text = content_div.get_text(separator=' ', strip=True)
            else:
                # fallback: body এর সব p ট্যাগ
                page_text = ' '.join([p.get_text() for p in soup.find_all('p')])

            page_text = final_clean(page_text)

            # যদি পেজে 50 ক্যারেক্টারের কম লেখা থাকে, তাহলে শেষ ধরে নিবো
            if len(page_text) < 50:
                print(f" Page {page_num} empty, ending book.")
                break

            full_book_text += page_text + "\n\n"
            print(f" Scraped page {page_num} -> {len(page_text)} chars")
            page_num += 1
            time.sleep(1.5) # সার্ভারে চাপ কমাতে

        except Exception as e:
            print(f" Error on ID {pamphlet_id} page {page_num}: {e}")
            break

    # ফাইল সেভ করা
    if full_book_text:
        safe_file_name = clean_folder_name(book_title) + ".txt"
        file_path = os.path.join(OUTPUT_FOLDER, safe_file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{book_title}\n")
            f.write(f"ID: {pamphlet_id}\n")
            f.write(f"Source: https://www.dawateislami.net/pamphlets/{pamphlet_id}\n")
            f.write("="*40 + "\n\n")
            f.write(full_book_text)
        print(f" -> Saved: {file_path}")
    else:
        print(f" -> No content found for ID {pamphlet_id}")

print("\nAll done!")
