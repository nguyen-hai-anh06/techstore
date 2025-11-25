import os  # IMPORT THƯ VIỆN HỆ THỐNG ĐỂ LÀM VIỆC VỚI HỆ ĐIỀU HÀNH VÀ ĐƯỜNG DẪN FILE

class Config:  # ĐỊNH NGHĨA LỚP CẤU HÌNH CHỨA TẤT CẢ CÁC THIẾT LẬP QUAN TRỌNG CHO ỨNG DỤNG
    SECRET_KEY = 'ecommerce-secret-key-2024'  # KHÓA BÍ MẬT DÙNG ĐỂ MÃ HÓA SESSION, COOKIES VÀ BẢO VỆ CSRF
    DATA_DIR = 'data'  # THƯ MỤC LƯU TRỮ TẤT CẢ CÁC FILE DỮ LIỆU JSON CỦA ỨNG DỤNG