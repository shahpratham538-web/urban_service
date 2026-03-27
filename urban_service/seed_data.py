"""
Seed script — populates the Urban Service platform with realistic test data.
Creates:
  • 3 service categories  (Plumbing, House Cleaning, Electrical)
  • 3 new provider users   (plumber, cleaner, electrician)
  • 6 services              (2 per provider)
  • 4 bookings by the test resident (various statuses)
  • 1 review + 1 payment   (for the completed booking)
  • 3 support tickets       (different priorities / statuses)
  • Notifications           (auto-created via helpers)

Run:  python seed_data.py
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urban_service.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import uuid

from core.models import User
from service.models import (
    Category, Service, Booking, Review, Payment,
    Ticket, Notification, create_notification,
)

# ======================================================================
#  HELPERS
# ======================================================================
def get_or_create_user(email, name, role, password, **extra):
    if User.objects.filter(email=email).exists():
        print(f"  [SKIP] {email} already exists")
        return User.objects.get(email=email)
    user = User.objects.create_user(email=email, password=password, name=name, role=role)
    for k, v in extra.items():
        setattr(user, k, v)
    user.save()
    print(f"  [OK]   Created {email} ({role})")
    return user


# ======================================================================
#  1. CATEGORIES
# ======================================================================
print("=" * 60)
print("1 · Creating service categories …")

categories_data = [
    {"name": "Plumbing",       "icon": "fa-wrench", "description": "Pipe repairs, drain cleaning, fixture installation and all water-related services."},
    {"name": "House Cleaning", "icon": "fa-broom",  "description": "Deep cleaning, regular maintenance, move-in/out cleaning services."},
    {"name": "Electrical",     "icon": "fa-bolt",   "description": "Wiring repairs, fixture installation, safety inspections and electrical services."},
]

categories = {}
for cd in categories_data:
    obj, created = Category.objects.get_or_create(
        name=cd["name"],
        defaults={"icon": cd["icon"], "description": cd["description"]},
    )
    categories[cd["name"]] = obj
    print(f"  {'[OK]  ' if created else '[SKIP]'} Category: {cd['name']}")


# ======================================================================
#  2. PROVIDER USERS
# ======================================================================
print("=" * 60)
print("2 · Creating provider users …")

provider_plumber = get_or_create_user(
    email="plumber@test.com", name="Raj Kumar",
    role="provider", password="provider123456",
)
provider_cleaner = get_or_create_user(
    email="cleaner@test.com", name="Priya Sharma",
    role="provider", password="provider123456",
)
provider_electrician = get_or_create_user(
    email="electrician@test.com", name="Amit Patel",
    role="provider", password="provider123456",
)


# ======================================================================
#  3. SERVICES  (2 per provider = 6 total)
# ======================================================================
print("=" * 60)
print("3 · Creating services …")

services_data = [
    # Plumbing
    {
        "serviceName": "Pipe Repair & Replacement",
        "serviceDescription": "Expert pipe repair and replacement service. We handle leaking pipes, burst pipes, and complete re-piping for kitchens, bathrooms, and outdoor plumbing. All work comes with a 30-day warranty.",
        "servicePrize": Decimal("500.00"),
        "provider": provider_plumber,
        "category": categories["Plumbing"],
    },
    {
        "serviceName": "Drain Cleaning & Unclogging",
        "serviceDescription": "Professional drain cleaning service using advanced equipment. We clear blocked drains in sinks, showers, and floor drains. Includes camera inspection for stubborn clogs.",
        "servicePrize": Decimal("350.00"),
        "provider": provider_plumber,
        "category": categories["Plumbing"],
    },
    # House Cleaning
    {
        "serviceName": "Deep Home Cleaning",
        "serviceDescription": "Complete deep cleaning of your entire home — living room, bedrooms, kitchen, and bathrooms. Includes floor scrubbing, appliance cleaning, window cleaning, and dusting of all surfaces.",
        "servicePrize": Decimal("800.00"),
        "provider": provider_cleaner,
        "category": categories["House Cleaning"],
    },
    {
        "serviceName": "Kitchen Deep Cleaning",
        "serviceDescription": "Intensive kitchen cleaning service. Covers chimney, gas stove, countertops, cabinets, sink, tiles, and floor. All food-safe cleaning products used.",
        "servicePrize": Decimal("450.00"),
        "provider": provider_cleaner,
        "category": categories["House Cleaning"],
    },
    # Electrical
    {
        "serviceName": "Electrical Wiring Repair",
        "serviceDescription": "Complete electrical wiring inspection and repair. We fix faulty wiring, short circuits, flickering lights, and overloaded circuits. All work follows safety code standards.",
        "servicePrize": Decimal("600.00"),
        "provider": provider_electrician,
        "category": categories["Electrical"],
    },
    {
        "serviceName": "Light & Fan Installation",
        "serviceDescription": "Professional installation of ceiling fans, chandeliers, LED panels, decorative lights, and exhaust fans. Includes wiring, mounting, and testing.",
        "servicePrize": Decimal("400.00"),
        "provider": provider_electrician,
        "category": categories["Electrical"],
    },
]

created_services = []
for sd in services_data:
    # Use serviceName + provider to avoid duplicates
    obj, created = Service.objects.get_or_create(
        serviceName=sd["serviceName"],
        provider=sd["provider"],
        defaults={
            "serviceDescription": sd["serviceDescription"],
            "servicePrize": sd["servicePrize"],
            "category": sd["category"],
            "is_active": True,
        },
    )
    created_services.append(obj)
    print(f"  {'[OK]  ' if created else '[SKIP]'} {sd['serviceName']} (₹{sd['servicePrize']})")


# ======================================================================
#  4. BOOKINGS  (by the test resident)
# ======================================================================
print("=" * 60)
print("4 · Creating sample bookings …")

resident = User.objects.filter(email="resident@test.com").first()

if not resident:
    print("  [WARN] resident@test.com not found — run create_test_users.py first!")
else:
    now = timezone.now()

    bookings_data = [
        {
            "service": created_services[0],   # Pipe Repair
            "status": "pending",
            "scheduled_date": now + timedelta(days=3),
            "notes": "Kitchen sink pipe is leaking. Please bring replacement parts.",
        },
        {
            "service": created_services[2],   # Deep Home Cleaning
            "status": "accepted",
            "scheduled_date": now + timedelta(days=5),
            "notes": "3 BHK apartment, need complete deep cleaning before a family event.",
        },
        {
            "service": created_services[4],   # Electrical Wiring Repair
            "status": "completed",
            "scheduled_date": now - timedelta(days=2),
            "notes": "Frequent short circuits in bedroom. Need full wiring check.",
        },
        {
            "service": created_services[5],   # Light & Fan Installation
            "status": "cancelled",
            "scheduled_date": now + timedelta(days=1),
            "notes": "Need 2 ceiling fans installed in new rooms.",
        },
    ]

    created_bookings = []
    for bd in bookings_data:
        # Avoid duplicating: check by service + resident + status
        existing = Booking.objects.filter(
            service=bd["service"], resident=resident, status=bd["status"]
        ).first()
        if existing:
            print(f"  [SKIP] Booking for {bd['service'].serviceName} ({bd['status']})")
            created_bookings.append(existing)
            continue

        booking = Booking.objects.create(
            service=bd["service"],
            resident=resident,
            scheduled_date=bd["scheduled_date"],
            status=bd["status"],
            notes=bd["notes"],
        )
        created_bookings.append(booking)
        print(f"  [OK]   Booking: {bd['service'].serviceName} → {bd['status']}")

        # Notify the provider
        create_notification(
            user=bd["service"].provider,
            message=f'New booking from {resident.name} for "{bd["service"].serviceName}".',
            notification_type='booking',
            link='/service/provider-bookings/',
        )

    # ------------------------------------------------------------------
    #  5. REVIEW + PAYMENT  (for the completed booking)
    # ------------------------------------------------------------------
    print("=" * 60)
    print("5 · Creating review & payment for completed booking …")

    completed_booking = created_bookings[2]  # Electrical Wiring Repair

    # Review
    if not hasattr(completed_booking, 'review') or not Review.objects.filter(booking=completed_booking).exists():
        Review.objects.create(
            booking=completed_booking,
            rating=5,
            comment="Amit was very professional and thorough. Fixed all the wiring issues quickly. Highly recommended!",
        )
        print("  [OK]   Review: 5★ for Electrical Wiring Repair")

        create_notification(
            user=completed_booking.service.provider,
            message=f'{resident.name} left a 5★ review for "{completed_booking.service.serviceName}".',
            notification_type='booking',
            link='/service/provider-reviews/',
        )
    else:
        print("  [SKIP] Review already exists")

    # Payment
    if not Payment.objects.filter(booking=completed_booking).exists():
        Payment.objects.create(
            booking=completed_booking,
            amount=completed_booking.service.servicePrize,
            status='completed',
            transaction_id=str(uuid.uuid4())[:12].upper(),
            paid_at=timezone.now(),
        )
        print(f"  [OK]   Payment: ₹{completed_booking.service.servicePrize} (completed)")

        create_notification(
            user=completed_booking.service.provider,
            message=f'Payment of ₹{completed_booking.service.servicePrize} received for "{completed_booking.service.serviceName}".',
            notification_type='payment',
            link='/service/provider-earnings/',
        )
    else:
        print("  [SKIP] Payment already exists")


# ======================================================================
#  6. SUPPORT TICKETS
# ======================================================================
print("=" * 60)
print("6 · Creating support tickets …")

support_user = User.objects.filter(role='support', is_active=True).first()
test_provider = User.objects.filter(email="provider@test.com").first()

tickets_data = [
    {
        "raised_by": resident if resident else None,
        "subject": "Service provider didn't show up on scheduled date",
        "description": "I booked a Deep Home Cleaning service for last Saturday but the provider did not arrive. I waited the entire morning. Please look into this and reschedule or refund.",
        "priority": "high",
        "status": "open",
        "assigned_to": None,
    },
    {
        "raised_by": test_provider,
        "subject": "Payment not received for completed booking",
        "description": "I completed a plumbing service 3 days ago but the payment still shows as pending. The resident confirmed they paid. Please check the transaction status.",
        "priority": "medium",
        "status": "in_progress",
        "assigned_to": support_user,
    },
    {
        "raised_by": resident if resident else None,
        "subject": "Wrong service category shown on listing",
        "description": "The 'Kitchen Deep Cleaning' service is showing under the wrong category when I filter by Plumbing. It should be under House Cleaning.",
        "priority": "low",
        "status": "open",
        "assigned_to": None,
    },
]

for td in tickets_data:
    if not td["raised_by"]:
        print(f"  [SKIP] Ticket '{td['subject']}' — user not found")
        continue

    existing = Ticket.objects.filter(subject=td["subject"], raised_by=td["raised_by"]).first()
    if existing:
        print(f"  [SKIP] Ticket: {td['subject']}")
        continue

    ticket = Ticket.objects.create(
        raised_by=td["raised_by"],
        assigned_to=td["assigned_to"],
        subject=td["subject"],
        description=td["description"],
        priority=td["priority"],
        status=td["status"],
    )
    print(f"  [OK]   Ticket: {td['subject']} ({td['priority']} / {td['status']})")

    # Notify support team
    if support_user:
        create_notification(
            user=support_user,
            message=f'New ticket raised: "{td["subject"]}" by {td["raised_by"].name}.',
            notification_type='ticket',
            link='/service/support-tickets/',
        )


# ======================================================================
#  SUMMARY
# ======================================================================
print("=" * 60)
print("✅  SEED DATA SUMMARY")
print(f"   Categories : {Category.objects.count()}")
print(f"   Providers  : {User.objects.filter(role='provider').count()}")
print(f"   Services   : {Service.objects.count()}")
print(f"   Bookings   : {Booking.objects.count()}")
print(f"   Reviews    : {Review.objects.count()}")
print(f"   Payments   : {Payment.objects.count()}")
print(f"   Tickets    : {Ticket.objects.count()}")
print(f"   Notifications: {Notification.objects.count()}")
print("=" * 60)

# Print login credentials for new providers
print()
print("New Provider Login Credentials:")
print("-" * 40)
print("  plumber@test.com      / provider123456")
print("  cleaner@test.com      / provider123456")
print("  electrician@test.com   / provider123456")
print("-" * 40)
print("All done! 🚀")
