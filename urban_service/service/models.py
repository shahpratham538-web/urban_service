from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User


# ---------------------------------------------------------------------------
# Category – organizes services (e.g. Plumbing, Cleaning, Electrical)
# ---------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="CSS icon class name, e.g. 'fa-wrench'",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Service – a service offered by a provider
# ---------------------------------------------------------------------------
class Service(models.Model):
    serviceName = models.CharField(max_length=100)
    serviceDescription = models.TextField()
    servicePrize = models.DecimalField(max_digits=10, decimal_places=2)
    serviceImage = models.ImageField(upload_to='service_images/')

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )

    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'provider'},
        related_name="services",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.serviceName


# ---------------------------------------------------------------------------
# ProviderAvailability – working‑hours/schedule for a provider
# ---------------------------------------------------------------------------
class ProviderAvailability(models.Model):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'provider'},
        related_name="availability_slots",
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Provider Availabilities"
        unique_together = ("provider", "day_of_week", "start_time")
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.provider.name} – {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


# ---------------------------------------------------------------------------
# Booking – a resident books a service
# ---------------------------------------------------------------------------
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="bookings"
    )
    resident = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookings"
    )

    booking_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When the resident wants the service performed",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    notes = models.TextField(blank=True, help_text="Any special instructions")

    class Meta:
        ordering = ["-booking_date"]

    def __str__(self):
        return f"{self.service.serviceName} – {self.resident.name} ({self.status})"


# ---------------------------------------------------------------------------
# Review – feedback left by a resident after a booking is completed
# ---------------------------------------------------------------------------
class Review(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="review"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.booking} – {self.rating}★"


# ---------------------------------------------------------------------------
# Payment – tracks money flow for a booking
# ---------------------------------------------------------------------------
class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="payment"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} – ₹{self.amount} ({self.status})"


# ---------------------------------------------------------------------------
# Ticket – support tickets raised by residents or providers
# ---------------------------------------------------------------------------
class Ticket(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    raised_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tickets_raised"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'support'},
        related_name="tickets_assigned",
    )
    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tickets",
    )

    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.id} – {self.subject}"


# ---------------------------------------------------------------------------
# Message – communication between resident and provider on a booking
# ---------------------------------------------------------------------------
class Message(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender.name} on {self.booking} at {self.created_at}"


# ---------------------------------------------------------------------------
# Notification – in‑app notifications for all users
# ---------------------------------------------------------------------------
class Notification(models.Model):
    TYPE_CHOICES = (
        ('booking', 'Booking'),
        ('payment', 'Payment'),
        ('ticket', 'Ticket'),
        ('message', 'Message'),
        ('system', 'System'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='system'
    )
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, help_text="Optional URL to redirect to")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.name} – {self.notification_type}"


def create_notification(user, message, notification_type='system', link=''):
    """Helper to create a notification for a user."""
    Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        link=link,
    )


# ---------------------------------------------------------------------------
# SiteSettings – singleton platform configuration
# ---------------------------------------------------------------------------
class SiteSettings(models.Model):
    GATEWAY_CHOICES = (
        ('simulated', 'Simulated (Testing)'),
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
    )

    site_name = models.CharField(max_length=200, default='Urban Service Platform')
    support_email = models.EmailField(default='support@urbanservice.com')
    payment_gateway = models.CharField(
        max_length=20, choices=GATEWAY_CHOICES, default='simulated'
    )
    enable_notifications = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

