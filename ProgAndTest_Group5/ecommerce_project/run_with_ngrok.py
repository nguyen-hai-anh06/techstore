# run_with_ngrok.py
from app import app
from pyngrok import ngrok, conf
import threading
import time
import sys
import os

def check_dependencies():
    """Kiểm tra và cài đặt dependencies nếu cần"""
    try:
        import pyngrok
        print("✅ pyngrok đã được cài đặt")
        return True
    except ImportError:
        print("❌ pyngrok chưa được cài đặt!")
        print("🔧 Đang cài đặt pyngrok...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
            print("✅ Đã cài đặt pyngrok thành công!")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi cài đặt pyngrok: {e}")
            return False

def check_data_files():
    """Kiểm tra xem dữ liệu đã được khởi tạo chưa"""
    data_files = ['data/products.json', 'data/users.json', 'data/categories.json']
    for file in data_files:
        if not os.path.exists(file):
            print(f"❌ File dữ liệu {file} không tồn tại")
            return False
    print("✅ Tất cả file dữ liệu đã sẵn sàng")
    return True

def initialize_data():
    """Khởi tạo dữ liệu nếu cần"""
    if not check_data_files():
        print("🔄 Đang khởi tạo dữ liệu mẫu...")
        try:
            from init_data import init_sample_data
            init_sample_data()
            print("✅ Khởi tạo dữ liệu thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo dữ liệu: {e}")
            return False
    return True

def start_ngrok():
    """Khởi động ngrok tunnel"""
    try:
        # Khởi tạo ngrok tunnel
        public_url = ngrok.connect(5000)
        print("=" * 70)
        print("🌐 PUBLIC URL CHO CÔ GIÁO:")
        print(f"   {public_url}")
        print("=" * 70)
        print("📱 Gửi link này cho cô giáo để truy cập!")
        print("⏰ Link có hiệu lực trong 2-8 giờ")
        print("💡 Lưu ý: Mỗi lần chạy lại sẽ có link mới")
        print("=" * 70)
        
        # Giữ tunnel mở
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Đóng ngrok tunnel...")
        ngrok.kill()
    except Exception as e:
        print(f"❌ Lỗi ngrok: {e}")

def main():
    """Hàm chính"""
    print("🚀 KHỞI CHẠY PROJECT VỚI NGROK")
    print("=" * 50)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        print("❌ Không thể khởi chạy do thiếu dependencies")
        return
    
    # Khởi tạo dữ liệu
    if not initialize_data():
        print("❌ Không thể khởi tạo dữ liệu")
        return
    
    print("🎯 THÔNG TIN ỨNG DỤNG:")
    print("   👤 Admin:  admin@example.com / admin123")
    print("   👨‍💼 User:   user@example.com / user123")
    print("=" * 50)
    
    # Chạy ngrok trong thread riêng
    print("🔄 Đang khởi động ngrok...")
    ngrok_thread = threading.Thread(target=start_ngrok)
    ngrok_thread.daemon = True
    ngrok_thread.start()
    
    # Đợi một chút để ngrok khởi động
    time.sleep(2)
    
    print("🔥 Đang khởi chạy Flask application...")
    print("⏹️  Nhấn Ctrl+C để dừng ứng dụng")
    print("=" * 50)
    
    try:
        # Chạy Flask app
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Đóng ứng dụng...")
        ngrok.kill()
    except Exception as e:
        print(f"❌ Lỗi khi chạy Flask: {e}")
        ngrok.kill()

if __name__ == '__main__':
    main()