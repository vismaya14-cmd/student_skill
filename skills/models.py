from django.db import models
from django.contrib.auth.models import User

# Choices for categories
CATEGORY_CHOICES = [
    ('design', 'Design'),
    ('coding', 'Coding'),
    ('teaching', 'Teaching'),
    ('other', 'Other'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    skills_offered = models.TextField(blank=True, default='', help_text='Comma-separated list of skills')
    location = models.CharField(max_length=150, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

class ServicePost(models.Model):
    CATEGORY_CHOICES = [
        ('design', 'Design'),
        ('coding', 'Coding'),
        ('teaching', 'Teaching'),
        ('other', 'Other'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price_type = models.CharField(max_length=20, choices=[('free', 'Free'), ('paid', 'Paid'), ('negotiable', 'Negotiable')])
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Where is this service available?")
    custom_category = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.category == 'other' and self.custom_category:
            self.category = self.custom_category
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ServiceRequest(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    budget = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Free, ₹500, Negotiable')
    custom_category = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.category == 'other' and self.custom_category:
            self.category = self.custom_category
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.recipient} at {self.timestamp}"

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(ServicePost, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rating {self.rating} for {self.service.title}"
