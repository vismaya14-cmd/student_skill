import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from skills.models import Service, HelpRequest

def migrate_categories():
    mapping = {
        'design': 'graphic_design',
        'coding': 'programming',
        'teaching': 'tutoring',
        'writing': 'writing',
        'tutoring': 'tutoring'
    }
    
    # Update Services
    for obj in Service.objects.all():
        if obj.category in mapping:
            obj.category = mapping[obj.category]
            obj.save()
            print(f"Updated Service {obj.id}: {obj.category}")
            
    # Update Requests
    for obj in HelpRequest.objects.all():
        if obj.category in mapping:
            obj.category = mapping[obj.category]
            obj.save()
            print(f"Updated Request {obj.id}: {obj.category}")

if __name__ == '__main__':
    migrate_categories()
    print("Categories Successfully Migrated")
