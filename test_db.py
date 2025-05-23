from database import db

def test_registration():
    # Kiểm tra chức năng đăng ký người dùng mới
    success, message = db.register_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    print(f"Registration: {'Success' if success else 'Failed'} - {message}")

def test_login():
    # Kiểm tra chức năng đăng nhập
    success, result = db.login_user(
        email="test@example.com",
        password="password123"
    )
    print(f"Login: {'Success' if success else 'Failed'} - {result}")

if __name__ == "__main__":
    test_registration()
    test_login()