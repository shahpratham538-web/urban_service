from django.contrib import admin
from .models import (
    Category,
    Service,
    Booking,
    ProviderAvailability,
    Review,
    Payment,
    Ticket,
    Message,
    Notification,
    SiteSettings,
)


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("serviceName", "provider", "category", "servicePrize", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("serviceName",)


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("service", "resident", "status", "booking_date", "scheduled_date")
    list_filter = ("status",)
    search_fields = ("service__serviceName", "resident__name")


# ---------------------------------------------------------------------------
# ProviderAvailability
# ---------------------------------------------------------------------------
@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("provider", "day_of_week", "start_time", "end_time", "is_available")
    list_filter = ("day_of_week", "is_available")


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("booking", "rating", "created_at")
    list_filter = ("rating",)


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "status", "paid_at")
    list_filter = ("status",)


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "raised_by", "assigned_to", "priority", "status", "created_at")
    list_filter = ("status", "priority")


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("booking", "sender", "created_at")
    list_filter = ("created_at",)


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__name", "message")


# ---------------------------------------------------------------------------
# SiteSettings
# ---------------------------------------------------------------------------
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "support_email", "payment_gateway", "enable_notifications", "maintenance_mode")

