import json
import re
import os

input_path = '/storage/emulated/0/Download/text/convert.txt'
output_path = '/storage/emulated/0/Download/text/converted_data.json'

def convert_txt_to_json():
    try:
        if not os.path.exists(input_path):
            print(f"ভুল: ফাইল পাওয়া যায়নি!")
            return

        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # নতুন লজিক: '1' এর পর থেকে পরবর্তী '1' এর আগ পর্যন্ত যা থাকবে 
        # তাকে আলাদা করা। এটি লাইনের শুরু বা মাঝখানের '1' কেউ গুরুত্ব দেবে।
        sections = re.split(r'\n(?=1)', content)
        
        # যদি প্রথম লাইনে '1' থাকে তবে split এর ফলে প্রথম এলিমেন্ট খালি হতে পারে
        if sections and not sections[0].startswith('1'):
            sections.pop(0)

        json_output = []
        for section in sections:
            if section.startswith('1'):
                # '1' বাদ দিয়ে প্রথম লাইনটি হেডিং হিসেবে নেওয়া
                lines = section[1:].split('\n', 1)
                heading = lines[0].strip()
                
                # বাকি অংশটুকু কন্টেন্ট
                body = lines[1].strip() if len(lines) > 1 else ""
                
                entry = {
                    "1": heading,
                    "2": body
                }
                json_output.append(entry)

        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_output, json_file, ensure_ascii=False, indent=4)
        
        print(f"সফল হয়েছে! {len(json_output)}টি এন্ট্রি তৈরি হয়েছে।")

    except Exception as e:
        print(f"ত্রুটি: {e}")

if __name__ == "__main__":
    convert_txt_to_json()
