from utils.db import SimpleDB
from utils.auth import SimpleAuth

def init_sample_data():
    db = SimpleDB()
    
    # Categories - Thêm đầy đủ danh mục
    categories = [
        {"id": 1, "name": "Điện thoại", "parent_id": None},
        {"id": 2, "name": "Laptop", "parent_id": None},
        {"id": 3, "name": "Tablet", "parent_id": None},
        {"id": 4, "name": "Apple", "parent_id": 1},
        {"id": 5, "name": "Samsung", "parent_id": 1},
        {"id": 6, "name": "Xiaomi", "parent_id": 1},
        {"id": 7, "name": "Gaming", "parent_id": None},
        {"id": 8, "name": "Phụ kiện", "parent_id": None}
    ]
    db.save('categories.json', categories)
    
    # Products - Thêm 10 sản phẩm với đầy đủ hình ảnh
    products = [
        {
            "id": 1,
            "name": "iPhone 15 Pro Max",
            "price": 32990000,
            "stock": 10,
            "category_id": 4,
            "description": "iPhone 15 Pro Max 256GB - Titanium, camera 48MP, Dynamic Island",
            "image": "/static/images/15-pro.jpg"
        },
        {
            "id": 2,
            "name": "Samsung Galaxy S24 Ultra", 
            "price": 28990000,
            "stock": 15,
            "category_id": 5,
            "description": "Samsung Galaxy S24 Ultra 256GB - Bút S-Pen, camera 200MP, AI",
            "image": "/static/images/samsungs24-ultra.jpg"
        },
        {
            "id": 3,
            "name": "MacBook Air M3",
            "price": 35990000,
            "stock": 8,
            "category_id": 2,
            "description": "MacBook Air M3 13 inch - 8GB RAM, 256GB SSD, viền mỏng",
            "image": "/static/images/macbookair-M3.jpg"
        },
        {
            "id": 4,
            "name": "iPad Pro M4",
            "price": 24990000,
            "stock": 12,
            "category_id": 3,
            "description": "iPad Pro M4 11 inch - Chip M4, màn hình Ultra Retina XDR",
            "image": "/static/images/ipad-pro-M4.jpg"
        },
        {
            "id": 5,
            "name": "Xiaomi Redmi Note 13",
            "price": 5990000,
            "stock": 20,
            "category_id": 6,
            "description": "Xiaomi Redmi Note 13 - Camera 108MP, chip Snapdragon, pin 5000mAh",
            "image": "/static/images/xiaomi-redmi-note-13.jpg"
        },
        {
            "id": 6,
            "name": "Dell XPS 13 Plus",
            "price": 41990000,
            "stock": 6,
            "category_id": 2,
            "description": "Dell XPS 13 Plus - Intel Core i7, 16GB RAM, 512GB SSD, OLED 3.5K",
            "image": "/static/images/dell-xps-13-plus.jpg"
        },
        {
            "id": 7,
            "name": "AirPods Pro 2",
            "price": 6990000,
            "stock": 25,
            "category_id": 8,
            "description": "AirPods Pro 2 - Chống ồn chủ động, chất lượng âm thanh spatial audio",
            "image": "/static/images/airpods-pro-2nd.jpg"
        },
        {
            "id": 8,
            "name": "Apple Watch Series 9",
            "price": 11990000,
            "stock": 18,
            "category_id": 8,
            "description": "Apple Watch Series 9 - Theo dõi sức khỏe, thể thao, GPS",
            "image": "/static/images/apple-watch-s9.jpg"
        },
        {
            "id": 9,
            "name": "Samsung Galaxy Tab S9",
            "price": 15990000,
            "stock": 10,
            "category_id": 3,
            "description": "Samsung Galaxy Tab S9 - Máy tính bảng cao cấp, bút S-Pen",
            "image": "/static/images/samsung-galaxy-tab-s9.jpg"
        },
        {
            "id": 10,
            "name": "PlayStation 5",
            "price": 11990000,
            "stock": 5,
            "category_id": 7,
            "description": "PlayStation 5 - Console gaming thế hệ mới, 4K 120Hz",
            "image": "/static/images/sony-playstation-5.jpg"
        }
    ]
    db.save('products.json', products)
    
    # Demo users
    auth = SimpleAuth()
    users = [
    {
        "id": 1,
        "name": "Admin",
        "email": "admin@example.com", 
        "password_hash": auth.hash_password("admin123"),
        "role": "admin"
    },
    {
        "id": 2, 
        "name": "Demo User",
        "email": "user@example.com",
        "password_hash": auth.hash_password("user123"),
        "role": "user"
    }
]
    db.save('users.json', users)

    # Empty files for other data
    db.save('carts.json', [])
    db.save('orders.json', [])
    db.save('order_items.json', [])

    print("✅ Dữ liệu mẫu đã được khởi tạo!")
    print("📦 Đã thêm 10 sản phẩm với đầy đủ hình ảnh")

if __name__ == "__main__":
    init_sample_data()