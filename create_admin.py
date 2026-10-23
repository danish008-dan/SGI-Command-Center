# create_admin.py
from database.user_queries import create_user

# Create the first administrator account
create_user(
    "Administrator",
    "admin@cms.com",
    "9999999999",
    "admin123",
    "Admin",
    None
)

print("Admin Created Successfully")