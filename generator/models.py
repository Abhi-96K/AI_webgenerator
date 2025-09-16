from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile for tracking usage and subscriptions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    websites_generated = models.IntegerField(default=0)
    free_websites_remaining = models.IntegerField(default=2)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free Plan'),
            ('basic', 'Basic Plan'),
            ('premium', 'Premium Plan'),
            ('enterprise', 'Enterprise Plan'),
        ],
        default='free'
    )
    subscription_expires = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Email verification with OTP
    email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    email_otp_created_at = models.DateTimeField(null=True, blank=True)
    email_otp_attempts = models.IntegerField(default=0)
    
    # Phone verification fields (for future implementation)
    phone_number = models.CharField(max_length=15, null=True, blank=True, help_text="Phone verification - Coming Soon!")
    phone_verified = models.BooleanField(default=False)
    phone_otp = models.CharField(max_length=6, null=True, blank=True)
    phone_otp_created_at = models.DateTimeField(null=True, blank=True)
    phone_otp_attempts = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription_plan}"

    def can_generate_website(self):
        """Check if user can generate a new website"""
        if self.subscription_plan != 'free':
            # Check if subscription is active
            if self.subscription_expires and self.subscription_expires > timezone.now():
                return True
            # If subscription expired, revert to free plan
            if self.subscription_expires and self.subscription_expires <= timezone.now():
                self.subscription_plan = 'free'
                self.save()
        
        # Free plan users
        return self.free_websites_remaining > 0

    def get_remaining_websites(self):
        """Get number of remaining websites user can generate"""
        if self.subscription_plan == 'free':
            return self.free_websites_remaining
        elif self.subscription_plan == 'basic':
            return 10  # Basic plan: 10 websites per month
        elif self.subscription_plan == 'premium':
            return 50  # Premium plan: 50 websites per month
        elif self.subscription_plan == 'enterprise':
            return 999  # Enterprise: virtually unlimited
        return 0

    def decrement_usage(self):
        """Decrement usage count when a website is generated"""
        if self.subscription_plan == 'free':
            if self.free_websites_remaining > 0:
                self.free_websites_remaining -= 1
        self.websites_generated += 1
        self.save()
    
    def generate_email_otp(self):
        """Generate a new 6-digit OTP for email verification"""
        import random
        from django.utils import timezone
        
        self.email_otp = str(random.randint(100000, 999999))
        self.email_otp_created_at = timezone.now()
        self.email_otp_attempts = 0
        self.save()
        return self.email_otp
    
    def verify_email_otp(self, otp):
        """Verify the provided OTP for email verification"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if OTP exists and hasn't expired (10 minutes)
        if not self.email_otp or not self.email_otp_created_at:
            return False, "No OTP found. Please request a new one."
        
        # Check expiration (10 minutes)
        if timezone.now() - self.email_otp_created_at > timedelta(minutes=10):
            return False, "OTP has expired. Please request a new one."
        
        # Check attempts limit (max 5 attempts)
        if self.email_otp_attempts >= 5:
            return False, "Too many attempts. Please request a new OTP."
        
        # Verify OTP
        if self.email_otp == otp:
            self.email_verified = True
            self.email_otp = None
            self.email_otp_created_at = None
            self.email_otp_attempts = 0
            self.user.is_active = True  # Activate the user account
            self.user.save()
            self.save()
            return True, "Email verified successfully!"
        else:
            self.email_otp_attempts += 1
            self.save()
            remaining = 5 - self.email_otp_attempts
            return False, f"Invalid OTP. {remaining} attempts remaining."
    
    def can_request_new_otp(self):
        """Check if user can request a new OTP (rate limiting)"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.email_otp_created_at:
            return True
        
        # Allow new OTP request after 2 minutes
        return timezone.now() - self.email_otp_created_at > timedelta(minutes=2)

class GeneratedSite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")],
        default="pending"
    )
    generated_file = models.FileField(upload_to="sites/", null=True, blank=True)  # zip file of generated website
    generated_code = models.TextField(null=True, blank=True)  # HTML code
    is_premium = models.BooleanField(default=False)  # Track if this was a premium generation
    generation_time = models.FloatField(null=True, blank=True)  # Time taken to generate
    downloads_count = models.IntegerField(default=0)  # Track download count

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} - {self.status} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']


class Suggestion(models.Model):
    """User suggestions for improvements"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, help_text="Your name")
    email = models.EmailField(help_text="Your email address")
    suggestion_type = models.CharField(
        max_length=20,
        choices=[
            ('feature', 'New Feature'),
            ('improvement', 'Improvement'),
            ('bug', 'Bug Report'),
            ('ui_ux', 'UI/UX Enhancement'),
            ('other', 'Other'),
        ],
        default='feature'
    )
    title = models.CharField(max_length=200, help_text="Brief title of your suggestion")
    description = models.TextField(help_text="Detailed description of your suggestion")
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Admin notes (internal)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    """Payment tracking for subscriptions"""
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('upi', 'UPI Payment'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('wallet', 'Digital Wallet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_reference = models.CharField(max_length=200, blank=True)
    qr_code_data = models.TextField(blank=True, help_text="QR code payment data")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    subscription_plan = models.CharField(max_length=20, blank=True)
    subscription_months = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
