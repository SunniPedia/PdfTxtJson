import json
import re
import os
import glob

# ফোল্ডার পাথ
input_dir = 'txt'
output_dir = 'json'

def convert_txt_to_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # '1' এর পর থেকে পরবর্তী '1' এর আগ পর্যন্ত আলাদা করা
        sections = re.split(r'\n(?=1)', content)
        
        if sections and not sections[0].startswith('1'):
            sections.pop(0)

        json_output = []
        for section in sections:
            if section.startswith('1'):
                lines = section[1:].split('\n', 1)
                heading = lines[0].strip()
                
                body = lines[1].strip() if len(lines) > 1 else ""
                
                entry = {
                    "1": heading,
                    "2": body
                }
                json_output.append(entry)

        # আউটপুট ফাইল পাথ তৈরি (txt এর নাম অনুযায়ী json তৈরি হবে)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.json")

        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_output, json_file, ensure_ascii=False, indent=4)
        
        print(f"সফল হয়েছে! '{base_name}.txt' থেকে {len(json_output)}টি এন্ট্রি তৈরি হয়েছে -> '{output_path}'")

    except Exception as e:
        print(f"ত্রুটি ({file_path}): {e}")

def process_all_files():
    # txt ফোল্ডার আছে কি না যাচাই
    if not os.path.exists(input_dir):
        print(f"ত্রুটি: '{input_dir}' ফোল্ডার পাওয়া যায়নি!")
        return

    # json ফোল্ডার না থাকলে তৈরি করে নিবে
    os.makedirs(output_dir, exist_ok=True)

    # txt ফোল্ডারের সব .txt ফাইল বের করা
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    if not txt_files:
        print(f"'{input_dir}' ফোল্ডারে কোনো .txt ফাইল পাওয়া যায়নি।")
        return

    for txt_file in txt_files:
        convert_txt_to_json(txt_file)

if __name__ == "__main__":
    process_all_files()
