from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Choices for location (cities)
LOCATION_CHOICES = [
    ('Mysore', 'Mysore'),
    ('Bangalore', 'Bangalore'),
    ('Mangalore', 'Mangalore'),
    ('Chennai', 'Chennai'),
    ('Hyderabad', 'Hyderabad'),
]

# Choices for service delivery type
SERVICE_TYPE_CHOICES = [
    ('Online', 'Online'),
    ('Offline', 'Offline'),
]

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

    # --- BADGE SYSTEM ---
    @property
    def is_top_seller(self):
        # Top seller if completed >= 5 jobs
        return self.user.received_requests.filter(status='completed').count() >= 5
        
    @property
    def is_fast_responder(self):
        # Fast responder if they have 100% acceptance or responded to > 3 requests
        return self.user.sent_messages.count() > 2

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

class Service(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=100, choices=LOCATION_CHOICES, help_text="City where this service is available")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='Online', help_text="Online or Offline delivery")
    
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash')
    delivery_time = models.CharField(max_length=50, choices=DELIVERY_CHOICES, default='negotiable')
    
    custom_category = models.CharField(max_length=50, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.category == 'other' and self.custom_category:
            self.category = self.custom_category
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def avg_rating(self):
        if hasattr(self, '_avg_rating'):
            return self._avg_rating
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return avg if avg else 0

    @avg_rating.setter
    def avg_rating(self, value):
        self._avg_rating = value

class HelpRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_requests')
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

class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('paid', 'Paid'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='requests')
    message = models.TextField(blank=True, null=True)
    payment = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')
    
    # --- FILE UPLOAD FEATURE ---
    requirement_file = models.FileField(upload_to='requirements/', blank=True, null=True, help_text="Added by requester")
    delivery_file = models.FileField(upload_to='deliveries/', blank=True, null=True, help_text="Added by provider")
    
    # --- MEETING SUPPORT ---
    meeting_link = models.URLField(blank=True, null=True, help_text="Video meeting link like Zoom/Meet")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        # Defensive check: sender and receiver might not be set during form validation
        try:
            if self.sender and self.receiver and self.sender == self.receiver:
                raise ValidationError("Sender and Receiver cannot be the same user.")
        except (User.DoesNotExist, AttributeError, models.ObjectDoesNotExist):
            pass

    def save(self, *args, **kwargs):
        # Removed self.full_clean() as it causes issues with commit=False and partial objects
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Request for {self.service.title} by {self.sender.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.receiver} regarding {self.service}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='author_id')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'service')


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='payments')
    # Link to the specific Request this payment belongs to (prevents duplicate payments)
    request = models.OneToOneField(
        'Request', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='request_payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[('upi', 'UPI'), ('card', 'Card'), ('cash', 'Cash')]
    )
    # --- PAYMENT INTEGRATION ---
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway = models.CharField(max_length=50, default='simulator', help_text='Stripe, Razorpay, Simulator')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.service.title} by {self.user.username}"

class Notification(models.Model):
    TYPES = [
        ('status', 'Status Change'),
        ('message', 'New Message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPES)
    related_request = models.ForeignKey('Request', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
