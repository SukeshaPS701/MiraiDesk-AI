from app.core.security import hash_password

password = "Mirai123"

hashed = hash_password(password)

print("Original :", password)
print("Hashed   :", hashed)