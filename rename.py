import os
import re

NAMES_FILE = "pamphlet_names.txt"
TXT_FOLDER = "pamphletTXT"

def clean_name(name):
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def load_mapping(filepath):
    mapping = {}
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found!")
        return mapping
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line or '|' not in line:
                continue
            pid, bname = line.split('|', 1)
            mapping[pid.strip()] = bname.strip()
    print(f"✅ Loaded {len(mapping)} Bangla names")
    return mapping

mapping = load_mapping(NAMES_FILE)

if not os.path.exists(TXT_FOLDER):
    print(f"❌ {TXT_FOLDER} folder not found!")
    exit(0)

renamed = 0
for filename in os.listdir(TXT_FOLDER):
    if not filename.endswith(".txt"):
        continue

    full_old = os.path.join(TXT_FOLDER, filename)

    # তোমার ফরম্যাট: important_8092.txt
    # এটা থেকে 8092 বের করা
    m = re.search(r'important_(\d+)\.txt$', filename, re.IGNORECASE)

    # যদি important_ না থাকে, fallback হিসেবে যেকোনো _number.txt
    if not m:
        m = re.search(r'_(\d+)\.txt$', filename)
    if not m:
        m = re.search(r'(\d+)\.txt$', filename)

    if not m:
        print(f"⏭️ Skip {filename} - number not found")
        continue

    pid = m.group(1)

    if pid not in mapping:
        print(f"⏭️ No Bangla name for {pid}, skipping {filename}")
        continue

    bangla_name = clean_name(mapping[pid])
    new_filename = f"{bangla_name}_{pid}.txt" # অকাট্য বিশ্বাসের বরকত_8092.txt
    # যদি চাও important_ টা রাখতে তাহলে: new_filename = f"important_{bangla_name}_{pid}.txt"

    full_new = os.path.join(TXT_FOLDER, new_filename)

    if full_old == full_new:
        print(f"✅ Already correct: {filename}")
        continue

    if os.path.exists(full_new):
        os.remove(full_new)

    os.rename(full_old, full_new)
    print(f"🔄 Renamed: {filename} -> {new_filename}")
    renamed += 1

print(f"\n=== Done! Renamed {renamed} files ===")
