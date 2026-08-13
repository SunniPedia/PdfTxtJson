import os
import time
import requests
from bs4 import BeautifulSoup
import html
import re

INPUT_FILE = "pamphlet.txt"
OUTPUT_FOLDER = "pamphletTXT"

BASE_URL = "https://www.dawateislami.net/pamphlets/{}/page/{}"

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

def run_git_command(cmd):
    return os.system(cmd)

def load_ids_from_txt(filepath):
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found!")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    ids = re.split(r'[,\n|\s]+', content)
    clean_ids = []
    for i in ids:
        i = i.strip()
        if i.isdigit():
            clean_ids.append(int(i))
    clean_ids = list(dict.fromkeys(clean_ids))
    print(f"Loaded {len(clean_ids)} IDs from {filepath}: {clean_ids}")
    return clean_ids

# GitHub Actions-এ Git User Config সেট করা
run_git_command('git config --global user.name "github-actions[bot]"')
run_git_command('git config --global user.email "github-actions[bot]@users.noreply.github.com"')

# pamphletTXT ফোল্ডার তৈরি করা
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PAMPHLET_IDS = load_ids_from_txt(INPUT_FILE)

for p_id in PAMPHLET_IDS:
    page = 1
    pamphlet_text = ""
    has_data = False
    book_title = ""
    print(f"\n========== Starting New Session for Pamphlet {p_id} ==========")

    while True:
        url = BASE_URL.format(p_id, page)
        print(f"Scraping Pamphlet {p_id} - Page {page}...")

        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code!= 200:
                print(f"Page {page} returned status {res.status_code}. Stopping pamphlet {p_id}.")
                break

            soup = BeautifulSoup(res.text, "html.parser")

            # প্রথম পেজে কিতাবের নাম খুঁজে বের করা (ফাইলের নামের জন্য)
            if page == 1:
                title_tag = soup.find("h1") or soup.find("h2") or soup.find("title")
                if title_tag:
                    book_title = title_tag.get_text(strip=True)

                if not book_title:
                    book_title = f"pamphlet_{p_id}"
                else:
                    book_title = f"{clean_folder_name(book_title)}_{p_id}"

                # চেক করা যে এটি আগে pamphletTXT ফোল্ডারে স্ক্র্যাপ করা হয়েছে কিনা
                file_path = os.path.join(OUTPUT_FOLDER, f"{book_title}.txt")

                if os.path.exists(file_path):
                    print(f"Skipping Pamphlet {p_id}, already exists at {file_path}")
                    break

            div = soup.find("div", class_="WordSection1")
            if not div:
                print(f"No WordSection1 div found on page {page}. Stopping pamphlet {p_id}.")
                break

            paragraphs = div.find_all("p")
            page_text = ""

            for p in paragraphs:
                raw_text = p.get_text(separator=' ', strip=True)
                cleaned_text = final_clean(raw_text)
                if cleaned_text:
                    page_text += cleaned_text + "\n\n"

            if page_text.strip():
                pamphlet_text += page_text
                has_data = True
                page += 1
            else:
                print(f"No valid text on page {page}. Stopping pamphlet {p_id}.")
                break

            time.sleep(0.5)

        except Exception as e:
            print(f"Error on Pamphlet {p_id}, Page {page}: {e}")
            break

    # প্রতিটি কিতাব আলাদা সেশনে pamphletTXT ফোল্ডারে সেভ ও পুশ করা
    if has_data and pamphlet_text.strip():
        try:
            file_path = os.path.join(OUTPUT_FOLDER, f"{book_title}.txt")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pamphlet_text)
            print(f"Saved: {file_path}")

            # প্রতিটা কিতাব আলাদা আলাদা সেশনে Commit এবং Push
            run_git_command(f'git add "{file_path}"')
            run_git_command(f'git add "{OUTPUT_FOLDER}"')
            run_git_command(f'git commit -m "Add pamphlet {p_id}: {book_title}"')
            run_git_command('git push')

            print(f"Pushed Pamphlet {p_id} to GitHub successfully in separate session.\n")
            print(f"========== Session Ended for Pamphlet {p_id} ==========\n")

        except Exception as e:
            print(f"Save/Push error for Pamphlet {p_id}: {e}\n")
    else:
        print(f"No data to save for Pamphlet {p_id}\n")
