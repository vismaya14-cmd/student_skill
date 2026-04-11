from django.db import models
from django.contrib.auth.models import User

# Choices for categories
CATEGORY_CHOICES = [
    ('programming', 'Programming'),
    ('web_dev', 'Web Development'),
    ('app_dev', 'App Development'),
    ('graphic_design', 'Graphic Design'),
    ('video_editing', 'Video Editing'),
    ('writing', 'Content Writing'),
    ('tutoring', 'Tutoring'),
    ('assignment', 'Assignment Help'),
    ('presentation', 'Presentation Design'),
    ('resume', 'Resume Making'),
    ('exam_prep', 'Exam Preparation'),
    ('other', 'Other'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default='')
    skills_offered = models.TextField(blank=True, default='', help_text='Comma-separated list of skills')
    location = models.CharField(max_length=150, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def skills_list(self):
        if self.skills_offered:
            return [s.strip() for s in self.skills_offered.split(',')]
        return []

    def __str__(self):
        return f'{self.user.username} Profile'

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('upi', 'UPI'),
    ('online', 'Online'),
]

PAYMENT_TYPE_CHOICES = [
    ('free', 'Free'),
    ('paid', 'Paid'),
    ('negotiable', 'Negotiable'),
]

DELIVERY_CHOICES = [
    ('instant', 'Instant / Urgent'),
    ('24h', 'Within 24 Hours'),
    ('2-3d', '2-3 Business Days'),
    ('1w', 'Within 1 Week'),
    ('negotiable', 'Flexible / Negotiable'),
]

class ServicePost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Where is this service available?")
    
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash')
    delivery_time = models.CharField(max_length=50, choices=DELIVERY_CHOICES, default='negotiable')
    
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

class ServiceBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_bookings')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_bookings')
    service = models.ForeignKey(ServicePost, on_delete=models.CASCADE, related_name='bookings')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking for {self.service.title} by {self.sender.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    service = models.ForeignKey(ServicePost, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.receiver} regarding {self.service}"

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(ServicePost, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    service = models.ForeignKey(ServicePost, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('upi', 'UPI'), ('card', 'Card'), ('cash', 'Cash')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.service.title} by {self.user.username}"
