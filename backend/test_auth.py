from auth_service import create_user, verify_user

# Create a test account
user_id = create_user(
    "third User",
    "eight@example.com",
    "TestPassword123"
)

print("User created with ID:", user_id)

# Test login
user = verify_user(
    "eight@example.com",
    "TestPassword123"
)

if user:
    print("Login test successful!")
    print(user)
else:
    print("Login test failed!")