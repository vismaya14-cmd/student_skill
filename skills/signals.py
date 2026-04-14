from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Message, Request, Notification

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.receiver,
            title=f"New Message from @{instance.sender.username}",
            message=instance.message[:50] + ("..." if len(instance.message) > 50 else ""),
            notif_type='message',
            related_request=instance.request
        )

@receiver(post_save, sender=Request)
def create_status_notification(sender, instance, **kwargs):
    # This signal creates notifications for status changes
    # Logic: Only notify if status is not 'pending' (the initial state)
    if instance.status == 'pending':
        # Notify the service provider (receiver) of a new inquiry
        title = "New Service Request! 📨"
        target_user = instance.receiver
        msg = f"@{instance.sender.username} wants to book your service '{instance.service.title}'."
    elif instance.status == 'accepted':
        title = "Request Accepted! 🎉"
        target_user = instance.sender
        msg = f"Your request for '{instance.service.title}' has been accepted."
    elif instance.status == 'paid':
        title = "Payment Received! 💳"
        target_user = instance.receiver
        msg = f"Payment for '{instance.service.title}' has been confirmed."
    elif instance.status == 'in_progress':
        title = "Service In Progress 🚀"
        target_user = instance.sender
        msg = f"Your service '{instance.service.title}' is now in progress."
    elif instance.status == 'rejected':
        title = "Request Declined"
        target_user = instance.sender
        msg = f"Your request for '{instance.service.title}' was declined."
    elif instance.status == 'completed':
        title = "Service Completed! ✅"
        target_user = instance.receiver
        msg = f"@{instance.sender.username} marked the service '{instance.service.title}' as completed."
    else:
        return

    # To prevent duplicate notifications on every save, we could check if one already exists
    # for this request and this status. For now, we'll keep it simple.
    Notification.objects.get_or_create(
        user=target_user,
        title=title,
        message=msg,
        notif_type='status',
        related_request=instance,
        is_read=False
    )
