from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from utils.db import SimpleDB
from utils.auth import SimpleAuth
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ecommerce-secret-key-2024'

db = SimpleDB()
auth = SimpleAuth()

# Helper functions
def format_currency(amount):
    # Định nghĩa hàm nhận một giá trị số (amount)
    # Trả về chuỗi đã được định dạng với dấu phẩy phân cách hàng nghìn,
    # không có phần thập phân và thêm ký hiệu tiền tệ "₫" ở cuối.
    return f"{amount:,.0f} ₫"

# Đăng ký bộ lọc Jinja2 tên 'currency' để dùng trong template: {{ value|currency }}
app.jinja_env.filters['currency'] = format_currency

def get_cart_count():
    # Nếu session không chứa 'user_id' (người dùng chưa đăng nhập), trả về 0.
    if 'user_id' not in session:
        return 0
    
    # Đọc danh sách giỏ hàng từ file carts.json (db.load trả về [] nếu file không tồn tại).
    carts = db.load('carts.json')
    # Tìm giỏ hàng của user hiện tại mà đang active (True).
    # Sử dụng next(..., None) để lấy phần tử đầu tiên thỏa điều kiện hoặc None nếu không có.
    user_cart = next((c for c in carts if c['user_id'] == session['user_id'] and c['active']), None)
    
    # Nếu không tìm thấy giỏ hàng active cho user, trả về 0.
    if not user_cart:
        return 0
    
    # Đọc danh sách item trong giỏ từ cart_items.json.
    cart_items = db.load('cart_items.json')
    # Lọc ra các item có cart_id khớp với id của giỏ hàng tìm được.
    user_items = [item for item in cart_items if item['cart_id'] == user_cart['id']]
    # Tổng số lượng hàng trong giỏ: cộng trường 'quantity' của từng item.
    return sum(item['quantity'] for item in user_items)
def require_admin():
    # Kiểm tra xem người dùng đã đăng nhập chưa và có vai trò là admin không
    if 'user_id' not in session or session.get('role') != 'admin':
        # Nếu không, hiển thị thông báo lỗi
        flash('Bạn không có quyền truy cập trang này!', 'error')
        # Chuyển hướng về trang chính
        return redirect(url_for('home'))

def require_login():
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if 'user_id' not in session:
        # Nếu chưa, hiển thị thông báo yêu cầu đăng nhập
        flash('Vui lòng đăng nhập!', 'error')
        # Chuyển hướng đến trang đăng nhập
        return redirect(url_for('login'))

# ==================== ROUTES ====================

@app.route('/')
def home():
    # Tải danh sách tất cả sản phẩm từ file products.json
    products = db.load('products.json')
    # Trả về trang chính (index.html) với danh sách sản phẩm và số lượng giỏ hàng hiện tại
    return render_template('index.html', products=products, cart_count=get_cart_count())

# ==================== AUTHENTICATION ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Kiểm tra xem yêu cầu là GET (hiển thị form) hay POST (xử lý đăng ký)
    if request.method == 'POST':
        # Lấy dữ liệu từ form: tên, email và mật khẩu
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Tải danh sách tất cả người dùng từ file users.json
        users = db.load('users.json')
        
        # Kiểm tra xem email đã tồn tại trong hệ thống chưa
        if any(user['email'] == email for user in users):
            # Nếu email tồn tại, hiển thị thông báo lỗi
            flash('Email đã tồn tại!', 'error')
            # Trả về form đăng ký
            return render_template('register.html')
        
        # Tạo đối tượng người dùng mới với các thông tin:
        new_user = {
            'id': db.get_next_id(users),  # ID tự động tăng
            'name': name,  # Tên người dùng
            'email': email,  # Email người dùng
            'password_hash': auth.hash_password(password),  # Mã hóa mật khẩu
            'role': 'user'  # Vai trò mặc định là người dùng thường
        }
        # Thêm người dùng mới vào danh sách
        users.append(new_user)
        # Lưu danh sách người dùng cập nhật vào file
        db.save('users.json', users)
        
        # Hiển thị thông báo đăng ký thành công
        flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
        # Chuyển hướng đến trang đăng nhập
        return redirect(url_for('login'))
    
    # Nếu là yêu cầu GET, hiển thị form đăng ký
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Kiểm tra xem yêu cầu là GET (hiển thị form) hay POST (xử lý đăng nhập)
    if request.method == 'POST':
        # Lấy email từ form đăng nhập
        email = request.form['email']
        # Lấy mật khẩu từ form đăng nhập
        password = request.form['password']
        
        # Tải danh sách tất cả người dùng từ file users.json
        users = db.load('users.json')
        # Tìm người dùng có email khớp với email nhập vào, trả về None nếu không tìm thấy
        user = next((u for u in users if u['email'] == email), None)
        
        # Kiểm tra xem người dùng tồn tại và mật khẩu nhập vào có khớp với mật khẩu đã mã hóa không
        if user and auth.verify_password(password, user['password_hash']):
            # Lưu ID người dùng vào session
            session['user_id'] = user['id']
            # Lưu tên người dùng vào session
            session['user_name'] = user['name']
            # Lưu vai trò (admin hoặc user) vào session
            session['role'] = user['role']
            # Lưu email người dùng vào session
            session['user_email'] = user['email']
            
            # Kiểm tra xem người dùng có vai trò admin không
            if user['role'] == 'admin':
                # Hiển thị thông báo chào mừng dành cho admin
                flash(f'Chào mừng admin {user["name"]}!', 'success')
            else:
                # Hiển thị thông báo chào mừng dành cho người dùng thường
                flash(f'Chào mừng {user["name"]}!', 'success')
            # Chuyển hướng về trang chính
            return redirect(url_for('home'))
        else:
            # Nếu email hoặc mật khẩu không đúng, hiển thị thông báo lỗi
            flash('Email hoặc mật khẩu không đúng!', 'error')
    
    # Nếu là yêu cầu GET, hiển thị form đăng nhập
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Xóa tất cả dữ liệu session của người dùng hiện tại
    session.clear()
    # Hiển thị thông báo đã đăng xuất thành công
    flash('Đã đăng xuất!', 'info')
    # Chuyển hướng về trang chính
    return redirect(url_for('home'))

# ==================== PRODUCTS ====================

@app.route('/products')
def products():
    # Lấy tham số 'category' từ URL query string, chuyển đổi sang kiểu int, mặc định là None
    category_id = request.args.get('category', type=int)
    # Lấy tham số 'search' từ URL query string, mặc định là chuỗi rỗng nếu không có
    search = request.args.get('search', '')
    
    # Tải danh sách tất cả sản phẩm từ file products.json
    all_products = db.load('products.json')
    # Tải danh sách tất cả danh mục từ file categories.json
    categories = db.load('categories.json')
    
    # Khởi tạo danh sách sản phẩm được lọc bằng tất cả sản phẩm
    filtered_products = all_products
    
    # Nếu có category_id được chọn (người dùng lọc theo danh mục)
    if category_id:
        # Lấy tất cả ID danh mục con có parent_id bằng category_id hiện tại
        subcategory_ids = [cat['id'] for cat in categories if cat['parent_id'] == category_id]
        
        # Nếu tồn tại danh mục con
        if subcategory_ids:
            # Lọc sản phẩm có category_id nằm trong danh mục con
            filtered_products = [p for p in filtered_products if p['category_id'] in subcategory_ids]
        else:
            # Nếu không có danh mục con, lọc sản phẩm trực tiếp theo category_id
            filtered_products = [p for p in filtered_products if p['category_id'] == category_id]
    
    # Nếu có từ khóa tìm kiếm
    if search:
        # Lọc sản phẩm có tên chứa từ khóa tìm kiếm (không phân biệt hoa thường)
        filtered_products = [p for p in filtered_products if search.lower() in p['name'].lower()]
    
    # Trả về template products.html với dữ liệu:
    # - products: danh sách sản phẩm đã được lọc
    # - categories: danh sách tất cả danh mục
    # - selected_category: danh mục được chọn hiện tại
    # - search_query: từ khóa tìm kiếm
    # - cart_count: số lượng sản phẩm trong giỏ hàng
    return render_template('products.html', 
                         products=filtered_products,
                         categories=categories,
                         selected_category=category_id,
                         search_query=search,
                         cart_count=get_cart_count())

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Tải danh sách tất cả sản phẩm từ file products.json
    products = db.load('products.json')
    # Tìm sản phẩm có id khớp với product_id từ URL, trả về None nếu không tìm thấy
    product = next((p for p in products if p['id'] == product_id), None)
    
    # Kiểm tra xem sản phẩm có tồn tại không
    if not product:
        # Nếu không tồn tại, hiển thị thông báo lỗi
        flash('Sản phẩm không tồn tại!', 'error')
        # Chuyển hướng về trang danh sách sản phẩm
        return redirect(url_for('products'))
    
    # Trả về template product_detail.html với dữ liệu:
    # - product: thông tin chi tiết sản phẩm
    # - cart_count: số lượng sản phẩm trong giỏ hàng
    return render_template('product_detail.html', product=product, cart_count=get_cart_count())

# ==================== CART & ORDERS (USER) ====================

@app.route('/cart')
def cart():
    # Kiểm tra người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Tải danh sách tất cả giỏ hàng từ file carts.json
    carts = db.load('carts.json')
    # Tìm giỏ hàng của user hiện tại mà đang active (True), trả về None nếu không tìm thấy
    user_cart = next((c for c in carts if c['user_id'] == session['user_id'] and c['active']), None)
    
    # Nếu user không có giỏ hàng active, trả về template với dữ liệu rỗng
    if not user_cart:
        return render_template('cart.html', cart_items=[], total=0, cart_count=0)
    
    # Tải danh sách tất cả item trong giỏ từ file cart_items.json
    cart_items = db.load('cart_items.json')
    # Lọc ra các item thuộc giỏ hàng của user hiện tại
    user_items = [item for item in cart_items if item['cart_id'] == user_cart['id']]
    
    # Khởi tạo biến tính tổng giá trị giỏ hàng
    total = 0
    # Lặp qua từng item trong giỏ hàng của user
    for item in user_items:
        # Tìm sản phẩm có id khớp với product_id của item, trả về None nếu không tìm thấy
        product = next((p for p in db.load('products.json') if p['id'] == item['product_id']), None)
        # Nếu sản phẩm tồn tại
        if product:
            # Gán thông tin sản phẩm vào item
            item['product'] = product
            # Tính tiền từng dòng: giá sản phẩm × số lượng
            item['subtotal'] = product['price'] * item['quantity']
            # Cộng tiền từng dòng vào tổng
            total += item['subtotal']
    
    # Trả về template cart.html với dữ liệu: danh sách item, tổng tiền, và số lượng giỏ hàng
    return render_template('cart.html', cart_items=user_items, total=total, cart_count=get_cart_count())

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    # Kiểm tra xem người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Tải danh sách tất cả giỏ hàng từ file carts.json
    carts = db.load('carts.json')
    # Tìm giỏ hàng của user hiện tại mà đang active (True), trả về None nếu không tìm thấy
    user_cart = next((c for c in carts if c['user_id'] == session['user_id'] and c['active']), None)
    
    # Nếu user không có giỏ hàng active
    if not user_cart:
        # Tạo giỏ hàng mới với các thông tin:
        user_cart = {
            'id': db.get_next_id(carts),  # ID tự động tăng
            'user_id': session['user_id'],  # ID của user hiện tại
            'active': True  # Đánh dấu là giỏ hàng đang hoạt động
        }
        # Thêm giỏ hàng mới vào danh sách
        carts.append(user_cart)
        # Lưu danh sách giỏ hàng cập nhật vào file
        db.save('carts.json', carts)
    
    # Tải danh sách tất cả item trong giỏ từ file cart_items.json
    cart_items = db.load('cart_items.json')
    # Tìm item trong giỏ hàng của user có product_id khớp, trả về None nếu không tìm thấy
    existing_item = next((item for item in cart_items 
                         if item['cart_id'] == user_cart['id'] and item['product_id'] == product_id), None)
    
    # Nếu sản phẩm đã tồn tại trong giỏ hàng
    if existing_item:
        # Tăng số lượng sản phẩm lên 1
        existing_item['quantity'] += 1
    else:
        # Nếu sản phẩm chưa có trong giỏ, tạo item mới với các thông tin:
        new_item = {
            'id': db.get_next_id(cart_items),  # ID tự động tăng
            'cart_id': user_cart['id'],  # ID của giỏ hàng
            'product_id': product_id,  # ID của sản phẩm
            'quantity': 1  # Số lượng mặc định là 1
        }
        # Thêm item mới vào danh sách
        cart_items.append(new_item)
    
    # Lưu danh sách item trong giỏ cập nhật vào file
    db.save('cart_items.json', cart_items)
    # Hiển thị thông báo thành công
    flash('Đã thêm vào giỏ hàng!', 'success')
    # Chuyển hướng về trang trước đó hoặc về trang danh sách sản phẩm nếu không có trang trước
    return redirect(request.referrer or url_for('products'))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    # Kiểm tra xem người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Lấy số lượng mới từ form và chuyển đổi sang kiểu int
    new_quantity = int(request.form['quantity'])
    
    # Nếu số lượng nhập vào <= 0 (không hợp lệ), gọi hàm xóa sản phẩm khỏi giỏ
    if new_quantity <= 0:
        return remove_from_cart(item_id)
    
    # Tải danh sách tất cả item trong giỏ từ file cart_items.json
    cart_items = db.load('cart_items.json')
    # Tìm item có id khớp với item_id từ URL, trả về None nếu không tìm thấy
    item = next((item for item in cart_items if item['id'] == item_id), None)
    
    # Nếu tìm thấy item trong giỏ hàng
    if item:
        # Cập nhật số lượng mới cho item
        item['quantity'] = new_quantity
        # Lưu danh sách item cập nhật vào file
        db.save('cart_items.json', cart_items)
        # Hiển thị thông báo cập nhật thành công
        flash('Đã cập nhật giỏ hàng!', 'success')
    
    # Chuyển hướng về trang giỏ hàng
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    # Kiểm tra xem người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Tải danh sách tất cả item trong giỏ từ file cart_items.json
    cart_items = db.load('cart_items.json')
    # Lọc ra các item có id khác với item_id, loại bỏ item cần xóa
    cart_items = [item for item in cart_items if item['id'] != item_id]
    # Lưu danh sách item đã cập nhật (sau khi xóa) vào file
    db.save('cart_items.json', cart_items)
    # Hiển thị thông báo xóa sản phẩm thành công
    flash('Đã xóa sản phẩm khỏi giỏ hàng!', 'success')
    # Chuyển hướng về trang giỏ hàng
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Kiểm tra xem người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Kiểm tra xem yêu cầu là GET (hiển thị trang thanh toán) hay POST (xử lý thanh toán)
    if request.method == 'POST':
        # Tải danh sách tất cả giỏ hàng từ file carts.json
        carts = db.load('carts.json')
        # Tìm giỏ hàng của user hiện tại mà đang active (True), trả về None nếu không tìm thấy
        user_cart = next((c for c in carts if c['user_id'] == session['user_id'] and c['active']), None)
        
        # Nếu user không có giỏ hàng active
        if not user_cart:
            # Hiển thị thông báo giỏ hàng trống
            flash('Giỏ hàng trống!', 'error')
            # Chuyển hướng về trang giỏ hàng
            return redirect(url_for('cart'))
        
        # Tải danh sách tất cả item trong giỏ từ file cart_items.json
        cart_items = db.load('cart_items.json')
        # Lọc ra các item thuộc giỏ hàng của user hiện tại
        user_items = [item for item in cart_items if item['cart_id'] == user_cart['id']]
        
        # Kiểm tra xem giỏ hàng có item nào không
        if not user_items:
            # Hiển thị thông báo giỏ hàng trống
            flash('Giỏ hàng trống!', 'error')
            # Chuyển hướng về trang giỏ hàng
            return redirect(url_for('cart'))
        
        # Khởi tạo biến tính tổng giá trị đơn hàng
        total = 0
        # Tải danh sách tất cả sản phẩm từ file products.json
        products = db.load('products.json')
        
        # Lặp qua từng item trong giỏ hàng của user
        for item in user_items:
            # Tìm sản phẩm có id khớp với product_id của item, trả về None nếu không tìm thấy
            product = next((p for p in products if p['id'] == item['product_id']), None)
            # Nếu sản phẩm tồn tại
            if product:
                # Kiểm tra xem số lượng trong kho có đủ không
                if product['stock'] < item['quantity']:
                    # Hiển thị thông báo sản phẩm không đủ số lượng
                    flash(f'Sản phẩm {product["name"]} không đủ số lượng!', 'error')
                    # Chuyển hướng về trang giỏ hàng
                    return redirect(url_for('cart'))
                # Tính tiền từng dòng: giá sản phẩm × số lượng, cộng vào tổng
                total += product['price'] * item['quantity']
        
        # Tải danh sách tất cả đơn hàng từ file orders.json
        orders = db.load('orders.json')
        # Tạo đơn hàng mới với các thông tin:
        new_order = {
            'id': db.get_next_id(orders),  # ID tự động tăng
            'user_id': session['user_id'],  # ID của user hiện tại
            'total': total,  # Tổng giá trị đơn hàng
            'status': 'pending',  # Trạng thái mặc định là đang chờ xử lý
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Thời gian tạo đơn hàng
        }
        # Thêm đơn hàng mới vào danh sách
        orders.append(new_order)
        # Lưu danh sách đơn hàng cập nhật vào file
        db.save('orders.json', orders)
        
        # Tải danh sách tất cả item trong đơn hàng từ file order_items.json
        order_items = db.load('order_items.json')
        # Lặp qua từng item trong giỏ hàng của user
        for item in user_items:
            # Tìm sản phẩm có id khớp với product_id của item, trả về None nếu không tìm thấy
            product = next((p for p in products if p['id'] == item['product_id']), None)
            # Nếu sản phẩm tồn tại
            if product:
                # Tạo item mới cho đơn hàng với các thông tin:
                new_order_item = {
                    'id': db.get_next_id(order_items),  # ID tự động tăng
                    'order_id': new_order['id'],  # ID của đơn hàng vừa tạo
                    'product_id': item['product_id'],  # ID của sản phẩm
                    'quantity': item['quantity'],  # Số lượng sản phẩm
                    'price': product['price']  # Giá sản phẩm tại thời điểm đặt hàng
                }
                # Thêm item mới vào danh sách
                order_items.append(new_order_item)
                # Giảm số lượng sản phẩm trong kho
                product['stock'] -= item['quantity']
        
        # Lưu danh sách item trong đơn hàng cập nhật vào file
        db.save('order_items.json', order_items)
        # Lưu danh sách sản phẩm với số lượng kho đã cập nhật vào file
        db.save('products.json', products)
        
        # Đánh dấu giỏ hàng hiện tại là không còn hoạt động (đã thanh toán)
        user_cart['active'] = False
        # Lưu danh sách giỏ hàng cập nhật vào file
        db.save('carts.json', carts)
        
        # Loại bỏ tất cả item của giỏ hàng đã thanh toán khỏi danh sách
        cart_items = [item for item in cart_items if item['cart_id'] != user_cart['id']]
        # Lưu danh sách item trong giỏ cập nhật vào file
        db.save('cart_items.json', cart_items)
        
        # Hiển thị thông báo đặt hàng thành công
        flash('Đặt hàng thành công! Cảm ơn bạn đã mua sắm.', 'success')
        # Chuyển hướng đến trang lịch sử đơn hàng
        return redirect(url_for('order_history'))
    
    # ===== XỬ LÝ YÊU CẦU GET (HIỂN THỊ TRANG THANH TOÁN) =====
    
    # Tải danh sách tất cả giỏ hàng từ file carts.json
    carts = db.load('carts.json')
    # Tìm giỏ hàng của user hiện tại mà đang active (True), trả về None nếu không tìm thấy
    user_cart = next((c for c in carts if c['user_id'] == session['user_id'] and c['active']), None)
    
    # Kiểm tra xem user có giỏ hàng active không
    if not user_cart:
        # Hiển thị thông báo giỏ hàng trống
        flash('Giỏ hàng trống!', 'error')
        # Chuyển hướng về trang giỏ hàng
        return redirect(url_for('cart'))
    
    # Tải danh sách tất cả item trong giỏ từ file cart_items.json
    cart_items = db.load('cart_items.json')
    # Lọc ra các item thuộc giỏ hàng của user hiện tại
    user_items = [item for item in cart_items if item['cart_id'] == user_cart['id']]
    
    # Kiểm tra xem giỏ hàng có item nào không
    if not user_items:
        # Hiển thị thông báo giỏ hàng trống
        flash('Giỏ hàng trống!', 'error')
        # Chuyển hướng về trang giỏ hàng
        return redirect(url_for('cart'))
    
    # Khởi tạo biến tính tổng giá trị đơn hàng
    total = 0
    # Tải danh sách tất cả sản phẩm từ file products.json
    products = db.load('products.json')
    # Lặp qua từng item trong giỏ hàng của user
    for item in user_items:
        # Tìm sản phẩm có id khớp với product_id của item, trả về None nếu không tìm thấy
        product = next((p for p in products if p['id'] == item['product_id']), None)
        # Nếu sản phẩm tồn tại
        if product:
            # Tính tiền từng dòng: giá sản phẩm × số lượng, cộng vào tổng
            total += product['price'] * item['quantity']
    
    # Trả về template checkout.html với dữ liệu: tổng giá trị đơn hàng và số lượng giỏ hàng
    return render_template('checkout.html', total=total, cart_count=get_cart_count())

@app.route('/orders')
def order_history():
    # Kiểm tra xem người dùng đã đăng nhập chưa, nếu chưa thì chuyển hướng đến trang đăng nhập
    require_login()
    
    # Tải danh sách tất cả đơn hàng từ file orders.json
    orders = db.load('orders.json')
    # Lọc ra các đơn hàng của user hiện tại bằng cách so sánh user_id
    user_orders = [order for order in orders if order['user_id'] == session['user_id']]
    
    # Tải danh sách tất cả item trong đơn hàng từ file order_items.json
    order_items = db.load('order_items.json')
    # Tải danh sách tất cả sản phẩm từ file products.json
    products = db.load('products.json')
    
    # Lặp qua từng đơn hàng của user hiện tại
    for order in user_orders:
        # Lọc ra các item thuộc đơn hàng hiện tại bằng cách so sánh order_id
        order['order_items'] = [item for item in order_items if item['order_id'] == order['id']]
        # Lặp qua từng item trong đơn hàng
        for item in order['order_items']:
            # Tìm sản phẩm có id khớp với product_id của item, trả về None nếu không tìm thấy
            product = next((p for p in products if p['id'] == item['product_id']), None)
            # Nếu sản phẩm tồn tại
            if product:
                # Gán tên sản phẩm vào item để sử dụng trong template
                item['product_name'] = product['name']
    
    # Trả về template orders.html với dữ liệu: danh sách đơn hàng của user và số lượng giỏ hàng
    return render_template('orders.html', orders=user_orders, cart_count=get_cart_count())

# ==================== ADMIN ROUTES ====================

@app.route('/admin')  # Định tuyến URL '/admin' tới hàm admin_dashboard
def admin_dashboard():  # Định nghĩa hàm xử lý trang tổng quan của admin
    require_admin()  # Kiểm tra quyền: nếu không phải admin sẽ flash + redirect
    
    orders = db.load('orders.json')  # Đọc danh sách đơn hàng từ file orders.json
    products = db.load('products.json')  # Đọc danh sách sản phẩm từ file products.json
    users = db.load('users.json')  # Đọc danh sách người dùng từ file users.json
    
    stats = {  # Tạo dictionary chứa các chỉ số/thống kê để hiển thị trên dashboard
        'total_orders': len(orders),  # Tổng số đơn hàng (đếm phần tử trong orders)
        'total_products': len(products),  # Tổng số sản phẩm (đếm phần tử trong products)
        'total_users': len([u for u in users if u['role'] == 'user']),  # Tổng số người dùng có role 'user'
        'total_revenue': sum(order['total'] for order in orders),  # Tổng doanh thu: cộng trường 'total' của từng đơn
        'pending_orders': len([o for o in orders if o['status'] == 'pending'])  # Số đơn có trạng thái 'pending'
    }
    
    return render_template('admin/dashboard.html', stats=stats, cart_count=get_cart_count())  # Trả về template admin/dashboard.html với dữ liệu thống kê và số lượng giỏ hàng

@app.route('/admin/products')  # Định tuyến URL '/admin/products' tới hàm admin_products
def admin_products():  # Định nghĩa hàm xử lý trang quản lý sản phẩm của admin
    require_admin()  # Kiểm tra quyền: nếu không phải admin sẽ flash thông báo lỗi + redirect
    
    products = db.load('products.json')  # Đọc danh sách tất cả sản phẩm từ file products.json
    categories = db.load('categories.json')  # Đọc danh sách tất cả danh mục từ file categories.json
    
    return render_template('admin/products.html', products=products, categories=categories, cart_count=get_cart_count())  # Trả về template admin/products.html với dữ liệu: danh sách sản phẩm, danh mục, và số lượng giỏ hàng

@app.route('/admin/products/add', methods=['GET', 'POST'])  # TẠO ĐƯỜNG DẪN CHO TRANG THÊM SẢN PHẨM, CHẤP NHẬN CẢ 2 PHƯƠNG THỨC GET (HIỂN THỊ TRANG) VÀ POST (GỬI DỮ LIỆU)
def admin_add_product():  # ĐỊNH NGHĨA HÀM XỬ LÝ CHỨC NĂNG THÊM SẢN PHẨM
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ CHO PHÉP ADMIN SỬ DỤNG CHỨC NĂNG NÀY
    
    if request.method == 'POST':  # NẾU NGƯỜI DÙNG GỬI FORM (NHẤN NÚT "THÊM SẢN PHẨM")
        name = request.form['name']  # LẤY TÊN SẢN PHẨM TỪ FORM NGƯỜI DÙNG NHẬP
        price = int(request.form['price'])  # LẤY GIÁ SẢN PHẨM VÀ CHUYỂN THÀNH SỐ NGUYÊN (VÍ DỤ: 1000000)
        stock = int(request.form['stock'])  # LẤY SỐ LƯỢNG TỒN KHO VÀ CHUYỂN THÀNH SỐ NGUYÊN
        category_id = int(request.form['category_id'])  # LẤY ID DANH MỤC VÀ CHUYỂN THÀNH SỐ NGUYÊN
        description = request.form['description']  # LẤY MÔ TẢ SẢN PHẨM TỪ FORM
        image = request.form['image']  # LẤY ĐƯỜNG DẪN HÌNH ẢNH SẢN PHẨM
        
        products = db.load('products.json')  # ĐỌC DỮ LIỆU SẢN PHẨM HIỆN CÓ TỪ FILE JSON
        
        new_product = {  # TẠO ĐỐI TƯỢNG SẢN PHẨM MỚI VỚI ĐẦY ĐỦ THÔNG TIN
            'id': db.get_next_id(products),  # TỰ ĐỘNG TẠO ID MỚI (LỚN HƠN ID CAO NHẤT HIỆN TẠI + 1)
            'name': name,  # TÊN SẢN PHẨM
            'price': price,  # GIÁ SẢN PHẨM
            'stock': stock,  # SỐ LƯỢNG TỒN KHO
            'category_id': category_id,  # ID DANH MỤC SẢN PHẨM
            'description': description,  # MÔ TẢ CHI TIẾT SẢN PHẨM
            'image': image  # ĐƯỜNG DẪN HÌNH ẢNH
        }
        
        products.append(new_product)  # THÊM SẢN PHẨM MỚI VÀO DANH SÁCH SẢN PHẨM HIỆN CÓ
        db.save('products.json', products)  # LƯU DANH SÁCH SẢN PHẨM ĐÃ CẬP NHẬT VÀO FILE JSON
        
        flash('Thêm sản phẩm thành công!', 'success')  # HIỂN THỊ THÔNG BÁO THÀNH CÔNG CHO NGƯỜI DÙNG
        return redirect(url_for('admin_products'))  # CHUYỂN HƯỚNG VỀ TRANG QUẢN LÝ SẢN PHẨM
    
    categories = db.load('categories.json')  # NẾU LÀ REQUEST GET: LOAD DANH SÁCH DANH MỤC ĐỂ HIỂN THỊ TRONG FORM
    return render_template('admin/add_product.html', categories=categories, cart_count=get_cart_count())  # HIỂN THỊ TRANG FORM THÊM SẢN PHẨM VỚI DANH SÁCH DANH MỤC VÀ SỐ LƯỢNG GIỎ HÀNG

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])  # TẠO ĐƯỜNG DẪN ĐỘNG CHO TRANG SỬA SẢN PHẨM, VỚI product_id LÀ THAM SỐ TRONG URL
def admin_edit_product(product_id):  # ĐỊNH NGHĨA HÀM XỬ LÝ CHỨC NĂNG SỬA SẢN PHẨM, NHẬN product_id LÀM THAM SỐ
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ CHO PHÉP ADMIN SỬ DỤNG CHỨC NĂNG NÀY
    
    products = db.load('products.json')  # ĐỌC TOÀN BỘ DANH SÁCH SẢN PHẨM TỪ DATABASE
    product = next((p for p in products if p['id'] == product_id), None)  # TÌM SẢN PHẨM THEO ID SỬ DỤNG GENERATOR EXPRESSION
    
    if not product:  # KIỂM TRA NẾU KHÔNG TÌM THẤY SẢN PHẨM
        flash('Sản phẩm không tồn tại!', 'error')  # HIỂN THỊ THÔNG BÁO LỖI CHO NGƯỜI DÙNG
        return redirect(url_for('admin_products'))  # CHUYỂN HƯỚNG VỀ TRANG QUẢN LÝ SẢN PHẨM
    
    if request.method == 'POST':  # NẾU NGƯỜI DÙNG GỬI FORM CẬP NHẬT (NHẤN NÚT "LƯU THAY ĐỔI")
        product['name'] = request.form['name']  # CẬP NHẬT TÊN SẢN PHẨM TỪ DỮ LIỆU FORM
        product['price'] = int(request.form['price'])  # CẬP NHẬT GIÁ SẢN PHẨM VÀ CHUYỂN THÀNH SỐ NGUYÊN
        product['stock'] = int(request.form['stock'])  # CẬP NHẬT SỐ LƯỢNG TỒN KHO VÀ CHUYỂN THÀNH SỐ NGUYÊN
        product['category_id'] = int(request.form['category_id'])  # CẬP NHẬT ID DANH MỤC VÀ CHUYỂN THÀNH SỐ NGUYÊN
        product['description'] = request.form['description']  # CẬP NHẬT MÔ TẢ SẢN PHẨM
        product['image'] = request.form['image']  # CẬP NHẬT ĐƯỜNG DẪN HÌNH ẢNH
        
        db.save('products.json', products)  # LƯU TOÀN BỘ DANH SÁCH SẢN PHẨM ĐÃ ĐƯỢC CẬP NHẬT VÀO DATABASE
        flash('Cập nhật sản phẩm thành công!', 'success')  # HIỂN THỊ THÔNG BÁO THÀNH CÔNG
        return redirect(url_for('admin_products'))  # CHUYỂN HƯỚNG VỀ TRANG QUẢN LÝ SẢN PHẨM
    
    categories = db.load('categories.json')  # LOAD DANH SÁCH DANH MỤC ĐỂ HIỂN THỊ TRONG FORM CHỈNH SỬA
    return render_template('admin/edit_product.html', product=product, categories=categories, cart_count=get_cart_count())  # HIỂN THỊ TRANG CHỈNH SỬA VỚI DỮ LIỆU SẢN PHẨM HIỆN TẠI

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])  # TẠO ĐƯỜNG DẪN ĐỘNG CHO CHỨC NĂNG XÓA SẢN PHẨM, CHỈ CHẤP NHẬN PHƯƠNG THỨC POST ĐỂ ĐẢM BẢO BẢO MẬT
def admin_delete_product(product_id):  # ĐỊNH NGHĨA HÀM XỬ LÝ CHỨC NĂNG XÓA SẢN PHẨM, NHẬN product_id LÀM THAM SỐ
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ CHO PHÉP ADMIN THỰC HIỆN XÓA SẢN PHẨM
    
    products = db.load('products.json')  # ĐỌC TOÀN BỘ DANH SÁCH SẢN PHẨM TỪ DATABASE
    products = [p for p in products if p['id'] != product_id]  # TẠO DANH SÁCH MỚI CHỈ CHỨA CÁC SẢN PHẨM CÓ ID KHÁC VỚI ID CẦN XÓA
    
    db.save('products.json', products)  # LƯU DANH SÁCH SẢN PHẨM MỚI (ĐÃ LOẠI BỎ SẢN PHẨM CẦN XÓA) VÀO DATABASE
    flash('Xóa sản phẩm thành công!', 'success')  # HIỂN THỊ THÔNG BÁO THÀNH CÔNG CHO NGƯỜI DÙNG
    return redirect(url_for('admin_products'))  # CHUYỂN HƯỚNG VỀ TRANG QUẢN LÝ SẢN PHẨM

@app.route('/admin/orders')  # TẠO ĐƯỜNG DẪN CHO TRANG QUẢN LÝ ĐƠN HÀNG CỦA ADMIN
def admin_orders():  # ĐỊNH NGHĨA HÀM XỬ LÝ HIỂN THỊ DANH SÁCH ĐƠN HÀNG
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ CHO PHÉP ADMIN XEM TRANG NÀY
    
    orders = db.load('orders.json')  # ĐỌC DANH SÁCH TẤT CẢ ĐƠN HÀNG TỪ DATABASE
    order_items = db.load('order_items.json')  # ĐỌC DANH SÁCH CHI TIẾT CÁC MẶT HÀNG TRONG ĐƠN HÀNG
    products = db.load('products.json')  # ĐỌC DANH SÁCH SẢN PHẨM ĐỂ LẤY THÔNG TIN TÊN SẢN PHẨM
    users = db.load('users.json')  # ĐỌC DANH SÁCH NGƯỜI DÙNG ĐỂ LẤY TÊN KHÁCH HÀNG
    
    for order in orders:  # DUYỆT QUA TỪNG ĐƠN HÀNG ĐỂ BỔ SUNG THÔNG TIN CHI TIẾT
        order['user_name'] = next((u['name'] for u in users if u['id'] == order['user_id']), 'Unknown')  # TÌM TÊN NGƯỜI DÙNG THEO user_id VÀ GÁN VÀO ĐƠN HÀNG
        order['order_items'] = [item for item in order_items if item['order_id'] == order['id']]  # LỌC TẤT CẢ MẶT HÀNG THUỘC VỀ ĐƠN HÀNG NÀY
        for item in order['order_items']:  # DUYỆT QUA TỪNG MẶT HÀNG TRONG ĐƠN HÀNG
            product = next((p for p in products if p['id'] == item['product_id']), None)  # TÌM THÔNG TIN SẢN PHẨM THEO product_id
            if product:  # NẾU TÌM THẤY SẢN PHẨM
                item['product_name'] = product['name']  # BỔ SUNG TÊN SẢN PHẨM VÀO THÔNG TIN MẶT HÀNG
    
    return render_template('admin/orders.html', orders=orders, cart_count=get_cart_count())  # HIỂN THỊ TRANG QUẢN LÝ ĐƠN HÀNG VỚI DỮ LIỆU ĐÃ ĐƯỢC XỬ LÝ

@app.route('/admin/orders/<int:order_id>/update', methods=['POST'])  # TẠO ĐƯỜNG DẪN ĐỘNG ĐỂ CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG, CHỈ CHẤP NHẬN PHƯƠNG THỨC POST
def admin_update_order(order_id):  # ĐỊNH NGHĨA HÀM CẬP NHẬT ĐƠN HÀNG, NHẬN order_id TỪ URL
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ ADMIN ĐƯỢC CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG
    
    new_status = request.form['status']  # LẤY GIÁ TRỊ TRẠNG THÁI MỚI TỪ FORM NGƯỜI DÙNG GỬI LÊN
    orders = db.load('orders.json')  # ĐỌC TOÀN BỘ DANH SÁCH ĐƠN HÀNG TỪ DATABASE
    
    order = next((o for o in orders if o['id'] == order_id), None)  # TÌM ĐƠN HÀNG CẦN CẬP NHẬT THEO ID SỬ DỤNG GENERATOR EXPRESSION
    if order:  # KIỂM TRA NẾU TÌM THẤY ĐƠN HÀNG
        order['status'] = new_status  # CẬP NHẬT TRẠNG THÁI MỚI CHO ĐƠN HÀNG
        db.save('orders.json', orders)  # LƯU DANH SÁCH ĐƠN HÀNG ĐÃ CẬP NHẬT VÀO DATABASE
        flash('Cập nhật trạng thái đơn hàng thành công!', 'success')  # HIỂN THỊ THÔNG BÁO THÀNH CÔNG
    
    return redirect(url_for('admin_orders'))  # CHUYỂN HƯỚNG NGƯỜI DÙNG QUAY LẠI TRANG QUẢN LÝ ĐƠN HÀNG

@app.route('/admin/users')  # TẠO ĐƯỜNG DẪN CHO TRANG QUẢN LÝ NGƯỜI DÙNG CỦA ADMIN
def admin_users():  # ĐỊNH NGHĨA HÀM XỬ LÝ HIỂN THỊ DANH SÁCH NGƯỜI DÙNG
    require_admin()  # KIỂM TRA QUYỀN TRUY CẬP - CHỈ CHO PHÉP ADMIN XEM TRANG NÀY
    
    users = db.load('users.json')  # ĐỌC TOÀN BỘ DANH SÁCH NGƯỜI DÙNG TỪ DATABASE
    return render_template('admin/users.html', users=users, cart_count=get_cart_count())  # HIỂN THỊ TRANG QUẢN LÝ NGƯỜI DÙNG VỚI DỮ LIỆU ĐÃ LOAD

if __name__ == '__main__':  # KIỂM TRA NẾU FILE NÀY ĐƯỢC CHẠY TRỰC TIẾP (KHÔNG PHẢI IMPORT)
    try:  # THỬ THỰC HIỆN CÁC LỆNH TRONG KHỐI NÀY
        db.load('products.json')  # THỬ ĐỌC FILE PRODUCTS.JSON ĐỂ KIỂM TRA DATABASE CÓ TỒN TẠI KHÔNG
        print("=" * 50)  # IN DẤU = 50 LẦN ĐỂ TẠO ĐƯỜNG KẺ NGANG TRONG CONSOLE
        print("✅ ỨNG DỤNG ĐÃ SẴN SÀNG!")  # THÔNG BÁO ỨNG DỤNG ĐÃ SẴN SÀNG HOẠT ĐỘNG
        print("   Tài khoản demo:")  # HIỂN THỊ THÔNG TIN TÀI KHOẢN DEMO CHO NGƯỜI DÙNG
        print("   Admin: admin@example.com / admin123")  # TÀI KHOẢN ADMIN MẶC ĐỊNH
        print("   User:  user@example.com / user123")  # TÀI KHOẢN USER MẶC ĐỊNH
        print("=" * 50)  # ĐƯỜNG KẺ NGANG TIẾP THEO
        print("🌐 TRUY CẬP: http://localhost:5000")  # HIỂN THỊ URL ĐỂ TRUY CẬP ỨNG DỤNG
        print("=" * 50)  # ĐƯỜNG KẺ NGANG KẾT THÚC
    except Exception as e:  # BẮT LỖI NẾU CÓ NGOẠI LỆ XẢY RA TRONG KHỐI TRY
        print(f"Lỗi khi khởi tạo dữ liệu: {e}")  # IN THÔNG BÁO LỖI VÀ CHI TIẾT LỖI
        try:  # THỬ KHỞI TẠO LẠI DỮ LIỆU MẪU
            from init_data import init_sample_data  # IMPORT HÀM KHỞI TẠO DỮ LIỆU MẪU
            init_sample_data()  # GỌI HÀM TẠO DỮ LIỆU MẪU
            print("✅ Đã khởi tạo dữ liệu mẫu")  # THÔNG BÁO ĐÃ TẠO DỮ LIỆU MẪU THÀNH CÔNG
        except Exception as e2:  # BẮT LỖI NẾU KHÔNG THỂ KHỞI TẠO DỮ LIỆU MẪU
            print(f"Lỗi khi chạy init_data: {e2}")  # IN THÔNG BÁO LỖI KHỞI TẠO DỮ LIỆU
    
    app.run(debug=True, host='127.0.0.1', port=5000)  # KHỞI CHẠY MÁY CHỦ FLASK VỚI CHẾ ĐỘ DEBUG