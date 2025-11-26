'''
Crawl danh sách địa danh từ trang web du lịch Việt Nam
Bao gồm tên địa danh, địa chỉ, nội dung, ảnh
Sử dụng requests và BeautifulSoup để lấy tiêu đề địa danh
'''

import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm
import time
import os
import re

# Tên file output
OUTPUT_FILE = "data/raw/danh_sach_dia_danh_chi_tiet.csv"

# URL gốc để ghép link ảnh
BASE_URL = "https://csdl.vietnamtourism.gov.vn"
BEGIN_PAGE = 1
END_PAGE = 32

# Mở file CSV để ghi
# newline='' là bắt buộc khi làm việc với module csv
# encoding='utf-8-sig' để Excel đọc file UTF-8 (tiếng Việt) không bị lỗi
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
    
    # Tạo đối tượng writer
    writer = csv.writer(f)
    
    # Viết hàng tiêu đề (header)
    writer.writerow(["TenDiaDanh", "DiaChi", "NoiDung", "ImageURL"])

    # Dùng tqdm để xem tiến trình
    for page_num in tqdm(range(BEGIN_PAGE, END_PAGE + 1), desc="Đang cào các trang"):
        
        page_url = f"{BASE_URL}/index.php/search/?data=dest&page={page_num}"
        
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Tìm tất cả các "khối" chứa thông tin
            # Thay vì tìm từng thẻ lẻ, ta tìm thẻ "data-item" chứa tất cả
            items = soup.select("section.data-list1")
            
            if not items:
                print(f"\nKhông tìm thấy 'data-item' nào ở trang {page_num}, có thể cấu trúc web đã thay đổi.")
                continue

            # 2. Lặp qua từng khối để trích xuất
            for item in items:
                # Lấy tên địa danh
                title_tag = item.select_one("div.data-title a")
                title = title_tag.get_text().strip() if title_tag else "N/A"
                
                # Lấy địa chỉ
                address_tag = item.select_one("div.data-address")
                address = address_tag.get_text().strip() if address_tag else "N/A"
                if address.startswith("Địa chỉ:"):
                    address = address[len("Địa chỉ:"):].strip()

                # Lấy nội dung 
                # Selector: <div class="col-md-12 data-type">
                content_tag = item.select_one("div.data-type")
                # .get_text() sẽ tự động bỏ thẻ <i> và lấy nội dung text
                content = content_tag.get_text().strip() if content_tag else "N/A"
                
                # Nếu nội dung có 'Vị trí:', tách phần vị trí ra
                # - Nếu địa chỉ rỗng/N/A thì gán địa chỉ bằng phần vị trí
                # - Xóa phần 'Vị trí:' khỏi nội dung để tránh lặp
                location_marker = 'Vị trí:'
                if content != "N/A" and location_marker in content:
                    idx = content.find(location_marker)
                    # Lấy phần nằm ngay sau 'Vị trí:' (chỉ 1 dòng/đoạn đầu)
                    after = content[idx + len(location_marker):].strip()
                    # Lấy câu đầu tiên sau 'Vị trí:'
                    first_line = ""
                    if after:
                        m = re.search(r'(.+?[\.!\?…])(?=\s|$)', after)
                        if m:
                            first_line = m.group(1).strip()

                    # Nếu address chưa có giá trị hợp lệ thì dùng phần vị trí
                    if not address or address.upper() == 'N/A':
                        address = first_line if first_line else address
                        
                        # Xóa đoạn 'Vị trí:' và phần vị trí (câu đầu) khỏi content
                        newline_idx = content.find('\n', idx)
                        if newline_idx != -1:
                            content = (content[:idx] + ' ' + content[newline_idx+1:]).strip()

                # LẤY MỚI: Lấy link ảnh
                # Selector: <img class="img-thumbnail">
                img_tag = item.select_one("img.img-thumbnail")
                img_src = "N/A"
                if img_tag and img_tag.has_attr('src'):
                    img_src = img_tag['src']
                    # Ghép link tương đối thành link tuyệt đối
                    if img_src.startswith("/"):
                        img_src = f"{BASE_URL}{img_src}"
                
                # 3. Viết 1 hàng vào file CSV (theo header: TenDiaDanh, DiaChi, NoiDung, ImageURL)
                writer.writerow([title, address, content, img_src])

        except requests.RequestException as e:
            print(f"\nLỗi khi tải trang {page_num}: {e}")
        
        time.sleep(0.1) # Tạm dừng nhỏ

print("--------------------------------------------------")
print(f"Hoàn thành! Dữ liệu đã được lưu tại: {os.path.abspath(OUTPUT_FILE)}")