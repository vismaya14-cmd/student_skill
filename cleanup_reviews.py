import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from skills.models import Review

def clean_duplicates():
    dups = Review.objects.values('user', 'service').annotate(count=Count('id')).filter(count__gt=1)
    for d in dups:
        ids = list(Review.objects.filter(user=d['user'], service=d['service']).values_list('id', flat=True)[1:])
        Review.objects.filter(id__in=ids).delete()
        print(f"Deleted {len(ids)} duplicates for User {d['user']} on Service {d['service']}")

if __name__ == "__main__":
    clean_duplicates()
