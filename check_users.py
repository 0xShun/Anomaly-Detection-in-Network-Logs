#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webplatform.settings')
django.setup()

from authentication.models import AdminUser

def main():
    print("Currently registered accounts:")
    users = AdminUser.objects.all()
    print(f"Total accounts: {users.count()}")
    print()
    
    if users.count() == 0:
        print("No accounts found.")
        return
    
    for u in users:
        print(f"Username: {u.username}")
        print(f"Email: {u.email}")
        print(f"Full name: {u.first_name} {u.last_name}")
        print(f"Staff status: {u.is_staff}")
        print(f"Superuser: {u.is_superuser}")
        print(f"Admin: {u.is_admin}")
        print(f"Active: {u.is_active}")
        print(f"Date joined: {u.date_joined}")
        print(f"Last login: {u.last_login}")
        print(f"Login attempts: {u.login_attempts}")
        print(f"Last login IP: {u.last_login_ip}")
        print("-" * 40)

if __name__ == "__main__":
    main()
