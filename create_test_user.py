"""
Create test user for authentication
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from authentication.models import AdminUser

# Create test admin user
if not AdminUser.objects.filter(username='admin').exists():
    user = AdminUser.objects.create_user(
        username='admin',
        email='admin@sabpaisa.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='super_admin',
        is_staff=True,
        is_superuser=True
    )
    print(f"Created test user: {user.username}")
else:
    print("Test user already exists")

# Create additional test users
test_users = [
    ('operations', 'operations@sabpaisa.com', 'pass123', 'Operations', 'Manager', 'operations_manager'),
    ('settlement', 'settlement@sabpaisa.com', 'pass123', 'Settlement', 'Admin', 'settlement_admin'),
    ('viewer', 'viewer@sabpaisa.com', 'pass123', 'View', 'Only', 'viewer'),
]

for username, email, password, first_name, last_name, role in test_users:
    if not AdminUser.objects.filter(username=username).exists():
        user = AdminUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        print(f"Created test user: {user.username} ({role})")

print("\nTest users created successfully!")
print("\nLogin credentials:")
print("  Admin: admin@sabpaisa.com / admin123")
print("  Operations: operations@sabpaisa.com / pass123")
print("  Settlement: settlement@sabpaisa.com / pass123")
print("  Viewer: viewer@sabpaisa.com / pass123")