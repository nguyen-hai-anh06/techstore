import bcrypt  # IMPORT THƯ VIỆN BCRYPT ĐỂ MÃ HÓA VÀ XÁC THỰC MẬT KHẨU MỘT CÁCH AN TOÀN

class SimpleAuth:  # ĐỊNH NGHĨA LỚP XỬ LÝ XÁC THỰC VÀ BẢO MẬT MẬT KHẨU
    @staticmethod  # ĐÁNH DẤU ĐÂY LÀ PHƯƠNG THỨC TĨNH - KHÔNG CẦN TẠO INSTANCE ĐỂ SỬ DỤNG
    def hash_password(password):  # PHƯƠNG THỨC MÃ HÓA MẬT KHẨU THÀNH CHUỖI BĂM AN TOÀN
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # MÃ HÓA MẬT KHẨU SỬ DỤNG BCRYPT VÀ TRẢ VỀ CHUỖI ĐÃ MÃ HÓA
    
    @staticmethod  # ĐÁNH DẤU PHƯƠNG THỨC TĨNH
    def verify_password(password, hashed):  # PHƯƠNG THỨC KIỂM TRA MẬT KHẨU CÓ KHỚP VỚI CHUỖI ĐÃ MÃ HÓA KHÔNG
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))  # SO SÁNH MẬT KHẨU GỐC VỚI CHUỖI ĐÃ MÃ HÓA VÀ TRẢ VỀ TRUE/FALSE