"""
Script to run migrations and create test users for all roles.
Run: python create_test_users.py
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urban_service.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Step 1: Run makemigrations + migrate
from django.core.management import call_command

print("=" * 50)
print("Running makemigrations...")
call_command('makemigrations', verbosity=2)

print("=" * 50)
print("Running migrate...")
call_command('migrate', verbosity=1)

print("=" * 50)
print("Running system check...")
call_command('check')

# Step 2: Create test users
from core.models import User

test_users = [
    {
        'email': 'admin@test.com',
        'name': 'Test Admin',
        'role': 'admin',
        'password': 'admin123456',
        'is_staff': True,
        'is_admin': True,
    },
    {
        'email': 'provider@test.com',
        'name': 'Test Provider',
        'role': 'provider',
        'password': 'provider123456',
    },
    {
        'email': 'resident@test.com',
        'name': 'Test Resident',
        'role': 'resident',
        'password': 'resident123456',
    },
    {
        'email': 'support@test.com',
        'name': 'Test Support',
        'role': 'support',
        'password': 'support123456',
    },
]

print("=" * 50)
print("Creating test users...")

for user_data in test_users:
    email = user_data['email']
    password = user_data['password']

    if User.objects.filter(email=email).exists():
        print(f"  [SKIP] {email} already exists")
        continue

    user = User.objects.create_user(
        email=email,
        password=password,
        name=user_data['name'],
        role=user_data['role'],
    )
    if user_data.get('is_staff'):
        user.is_staff = True
    if user_data.get('is_admin'):
        user.is_admin = True
    user.save()
    print(f"  [OK]   Created {email} ({user_data['role']})")

print("=" * 50)
print("All done!")
