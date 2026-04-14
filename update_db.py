import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from skills.models import Service

def update_services():
    # Update Programming Service
    coding1 = Service.objects.filter(title__icontains='Programming').first()
    if coding1:
        coding1.image = 'service_images/coding.png'
        coding1.delivery_time = '2-3d'
        coding1.payment_method = 'online'
        coding1.save()
        print(f"Updated: {coding1.title}")

    # Update Tutoring Service
    t1 = Service.objects.filter(title='Tutoring').first()
    if t1:
        t1.image = 'service_images/tutoring.png'
        t1.delivery_time = '24h'
        t1.payment_method = 'cash'
        t1.save()
        print(f"Updated: {t1.title}")

    # Update Design Service
    d1 = Service.objects.filter(title__icontains='Design').first()
    if d1:
        d1.image = 'service_images/design.png'
        d1.delivery_time = '2-3d'
        d1.payment_method = 'upi'
        d1.save()
        print(f"Updated: {d1.title}")

    # Update AI Service
    coding2 = Service.objects.filter(title__icontains='AI based').first()
    if coding2:
        coding2.image = 'service_images/coding.png'
        coding2.delivery_time = '1w'
        coding2.payment_method = 'online'
        coding2.save()
        print(f"Updated: {coding2.title}")

if __name__ == '__main__':
    update_services()
    print("Database Updated with Realistic Data")
