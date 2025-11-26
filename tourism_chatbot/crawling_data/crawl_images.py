'''
Crawl ảnh địa danh từ Google Images sử dụng Selenium
Chia folder lưu ảnh theo tên địa danh
'''
import os
import time
import requests
import re
import unicodedata
import pandas as pd
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# --- 0. Chọn lọc các địa danh để crawl

data = pd.read_csv('data/raw/danh_sach_dia_danh_chi_tiet.csv')
data.columns

# keep rows where TenDiaDanh, DiaChi and ImageURL are non-null and not empty/whitespace
cols = ['TenDiaDanh', 'DiaChi', 'ImageURL']
filtered_data = data.dropna(subset=cols).copy()
for c in cols:
    filtered_data = filtered_data[filtered_data[c].astype(str).str.strip() != '']

filtered_data = filtered_data.reset_index(drop=True)
all_queries = filtered_data['TenDiaDanh'].tolist()

# --- 1. CẤU HÌNH (Bạn có thể thay đổi) ---

# File chứa danh sách địa danh
# LIST_FILE = "danh_sach_dia_danh.txt"

# Số lượng địa danh đầu tiên để chạy thử nghiệm
TEST_RUN_LIMIT = 100

NUM_SCROLLS = 3

# Giới hạn số ảnh tối đa cho mỗi địa danh (Để chạy nhanh hơn)
MAX_IMAGES_PER_QUERY = 50

# Ngưỡng kích thước ảnh
MIN_WIDTH = 400
MIN_HEIGHT = 400

# Thư mục chính để lưu tất cả ảnh
MAIN_DOWNLOAD_DIR = "data/raw/crawled_images"

# Các từ khóa "rác" cần bỏ qua (Giải quyết Rủi ro 1)
# BAD_KEYWORDS = ["Tỉnh", "Du lịch", "Thành phố", "Huyện"]

# Các selector của Google (Cần cập nhật khi Google thay đổi)
THUMBNAIL_SELECTOR = "div.H8Rx8c"   # Selector để click mở panel (div.YQ4gaf?)
HIGH_RES_SELECTOR = "img.iPVvYb"  # Selector ảnh HD trong panel (img.FyHeAf?)


# --- 2. HÀM SLUGIFY (Giải quyết Rủi ro 2) ---
def slugify(value):
    """
    Chuyển đổi chuỗi (có dấu, cách, ký tự đặc biệt) 
    thành một chuỗi an toàn để làm tên file/thư mục.
    Ví dụ: "Khu nhà công tử Bạc Liêu" -> "khu_nha_cong_tu_bac_lieu"
    """
    # Chuyển 'đ' thành 'd'
    value = str(value).replace("đ", "d").replace("Đ", "D")
    # Bỏ dấu tiếng Việt
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
    # Xóa ký tự đặc biệt, giữ lại chữ, số, khoảng trắng, gạch nối
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    # Thay thế khoảng trắng/gạch nối bằng 1 gạch dưới
    value = re.sub(r'[\s-]+', '_', value)
    return value

# --- 3. ĐỌC DANH SÁCH ĐỊA DANH ---
# try:
#     with open(LIST_FILE, 'r', encoding='utf-8') as f:
#         # Đọc tất cả các dòng, xóa khoảng trắng thừa
#         all_queries = [line.strip() for line in f if line.strip()]
# except FileNotFoundError:
#     print(f"LỖI: Không tìm thấy file '{LIST_FILE}'.")
#     print("Vui lòng đảm bảo file này nằm cùng thư mục với script.")
#     exit()

# Lấy 10 địa danh đầu tiên để chạy thử
queries_to_run = all_queries[:TEST_RUN_LIMIT]

print(f"--- BẮT ĐẦU CHẠY THỬ NGHIỆM VỚI {len(queries_to_run)} ĐỊA DANH ---")
if not os.path.exists(MAIN_DOWNLOAD_DIR):
    os.makedirs(MAIN_DOWNLOAD_DIR)

# --- 4. VÒNG LẶP CHÍNH ---
# Dùng tqdm để xem tiến trình
for query in tqdm(queries_to_run, desc="Tổng tiến trình"):
    
    # 4.1. Lọc từ khóa "rác" (Rủi ro 1)
    # if any(bad_word in query for bad_word in BAD_KEYWORDS):
    #     print(f"\n[Bỏ qua] Query chứa từ khóa rác: {query}")
    #     continue # Chuyển sang địa danh tiếp theo

    # 4.2. Tạo tên thư mục an toàn (Rủi ro 2)
    folder_name = slugify(query)
    query_download_dir = os.path.join(MAIN_DOWNLOAD_DIR, folder_name)

    # 4.3. Kiểm tra nếu đã tồn tại (Rủi ro 3)
    if os.path.exists(query_download_dir):
        print(f"\n[Đã tồn tại] Thư mục '{folder_name}' đã có. Bỏ qua.")
        continue # Chuyển sang địa danh tiếp theo

    # Nếu chưa tồn tại, tạo thư mục
    os.makedirs(query_download_dir)
    print(f"\n[Đang xử lý] Query: '{query}' (Lưu vào thư mục: '{folder_name}')")

    # 4.4. Khởi chạy Selenium cho query này
    driver = None # Khởi tạo driver là None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        wait = WebDriverWait(driver, 5)

        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        driver.get(search_url)

        # Scroll NUM_SCROLLS lần để tải thêm ảnh
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(NUM_SCROLLS):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Tìm tất cả thumbnails
        thumbnail_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, THUMBNAIL_SELECTOR))
        )
        print(f"  -> Tìm thấy {len(thumbnail_elements)} thumbnails.")

        image_count = 0 # Bộ đếm ảnh cho query này

        # 4.5. Lặp qua từng thumbnail
        for thumb_index in range(len(thumbnail_elements)):
            
            # Giải quyết Rủi ro 4: Dừng nếu đủ ảnh
            if image_count >= MAX_IMAGES_PER_QUERY:
                print(f"  -> Đã đạt giới hạn {MAX_IMAGES_PER_QUERY} ảnh. Chuyển sang địa danh tiếp theo.")
                break # Thoát vòng lặp thumbnail

            try:
                # Phải tìm lại element mỗi lần lặp để tránh lỗi "Stale"
                thumbnails = driver.find_elements(By.CSS_SELECTOR, THUMBNAIL_SELECTOR)
                if thumb_index >= len(thumbnails):
                    break
                
                thumbnails[thumb_index].click()
                
            except (StaleElementReferenceException, ElementClickInterceptedException):
                continue # Bỏ qua nếu click lỗi

            # 4.6. Chờ ảnh HD và tải về
            try:
                high_res_img = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, HIGH_RES_SELECTOR))
                )
                
                img_url = high_res_img.get_attribute('src')
                
                if img_url and img_url.startswith("http"):
                    response = requests.get(img_url, timeout=10)
                    
                    # Lọc kích thước
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data)
                    
                    if img.width >= MIN_WIDTH and img.height >= MIN_HEIGHT:
                        # Lưu ảnh
                        file_name = f"{folder_name}_{image_count + 1}.jpg"
                        file_path = os.path.join(query_download_dir, file_name)
                        
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        #print(f"    -> Đã lưu: {file_name}")
                        image_count += 1
                    else:
                        #print(f"    -> Bỏ qua (ảnh nhỏ: {img.width}x{img.height})")
                        pass
                        
            except Exception:
                #print("    -> Lỗi khi tải ảnh HD, bỏ qua.")
                pass # Bỏ qua nếu không tìm thấy ảnh HD
        
        print(f"  -> Hoàn thành '{query}'. Đã tải về {image_count} ảnh.")

    except Exception as e:
        print(f"\n[LỖI] Gặp sự cố nghiêm trọng khi xử lý '{query}': {e}")
    finally:
        # Đảm bảo trình duyệt luôn đóng, ngay cả khi gặp lỗi
        if driver:
            driver.quit()
    
    # Tạm dừng 1 giây giữa các địa danh để giảm nguy cơ bị chặn
    time.sleep(1)

print(f"\n--- HOÀN THÀNH CHẠY THỬ NGHIỆM ---")
print(f"Vui lòng kiểm tra thư mục: {MAIN_DOWNLOAD_DIR}")