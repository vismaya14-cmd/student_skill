from django.db import connection
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

def check_schema():
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(skills_review)")
        columns = cursor.fetchall()
        print("Schema for skills_review:")
        for col in columns:
            print(col)

if __name__ == "__main__":
    check_schema()
