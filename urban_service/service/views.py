import os
import json
import hmac
import hashlib

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.core.paginator import Paginator

from core.decorators import role_required
from .forms import (
    ServiceCreationForm, BookingForm, ReviewForm,
    TicketForm, AvailabilityForm, MessageForm, SiteSettingsForm,
)
from .models import (
    Booking, Service, Review, Payment, Ticket, Category,
    ProviderAvailability, Message, Notification, SiteSettings,
    create_notification,
)


# ==========================================================================
#  PROVIDER VIEWS
# ==========================================================================

@role_required(allowed_roles=['provider'])
def createService(request):
    if request.method == "POST":
        form = ServiceCreationForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            return redirect("provider_dashboard")
    else:
        form = ServiceCreationForm()
    return render(request, "service/provider/create_service.html", {"form": form})


@role_required(allowed_roles=['provider'])
def editService(request, service_id):
    """Provider can edit their own service."""
    service = get_object_or_404(Service, id=service_id, provider=request.user)
    if request.method == "POST":
        form = ServiceCreationForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            return redirect("provider_services")
    else:
        form = ServiceCreationForm(instance=service)
    return render(request, "service/provider/edit_service.html", {"form": form, "service": service})


@role_required(allowed_roles=['provider'])
def deleteService(request, service_id):
    """Provider can delete their own service."""
    service = get_object_or_404(Service, id=service_id, provider=request.user)
    if request.method == "POST":
        service.delete()
        return redirect("provider_services")
    return render(request, "service/provider/delete_service.html", {"service": service})


@role_required(allowed_roles=['provider'])
def providerServices(request):
    services = Service.objects.filter(provider=request.user)
    return render(request, "service/provider/provider_services.html", {"services": services})


@role_required(allowed_roles=['provider'])
def providerBookings(request):
    bookings = Booking.objects.filter(service__provider=request.user)
    return render(request, "service/provider/provider_bookings.html", {"bookings": bookings})


@role_required(allowed_roles=['provider'])
def updateBookingStatus(request, booking_id, status):
    """Only the provider who owns the service can update the booking status."""
    booking = get_object_or_404(Booking, id=booking_id)

    # Ownership check
    if booking.service.provider != request.user:
        return HttpResponseForbidden("You are not allowed to update this booking.")

    allowed_statuses = ['accepted', 'in_progress', 'completed', 'cancelled']
    if status in allowed_statuses:
        booking.status = status
        booking.save()

        # Notify resident about booking status change
        create_notification(
            user=booking.resident,
            message=f'Your booking for "{booking.service.serviceName}" has been {status}.',
            notification_type='booking',
            link=f'/service/my-bookings/',
        )

    return redirect("provider_bookings")


@role_required(allowed_roles=['provider'])
def providerEarnings(request):
    """Show a summary of the provider's completed-booking earnings."""
    paid_bookings = Payment.objects.filter(
        booking__service__provider=request.user,
        status='completed',
    ).select_related('booking__service', 'booking__resident')
    total_earnings = paid_bookings.aggregate(
        total=Sum('amount')
    )['total'] or 0
    return render(request, "service/provider/provider_earnings.html", {
        "paid_bookings": paid_bookings,
        "total_earnings": total_earnings,
    })


@role_required(allowed_roles=['provider'])
def manageAvailability(request):
    """List current slots and add new ones."""
    slots = ProviderAvailability.objects.filter(provider=request.user)

    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.provider = request.user
            slot.save()
            return redirect("manage_availability")
    else:
        form = AvailabilityForm()

    return render(request, "service/provider/manage_availability.html", {
        "slots": slots,
        "form": form,
    })


@role_required(allowed_roles=['provider'])
def editAvailability(request, slot_id):
    """Edit an existing availability slot."""
    slot = get_object_or_404(ProviderAvailability, id=slot_id, provider=request.user)
    if request.method == "POST":
        form = AvailabilityForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect("manage_availability")
    else:
        form = AvailabilityForm(instance=slot)
    return render(request, "service/provider/edit_availability.html", {"form": form, "slot": slot})


@role_required(allowed_roles=['provider'])
def deleteAvailability(request, slot_id):
    """Delete an availability slot."""
    slot = get_object_or_404(ProviderAvailability, id=slot_id, provider=request.user)
    if request.method == "POST":
        slot.delete()
        return redirect("manage_availability")
    return render(request, "service/provider/delete_availability.html", {"slot": slot})


@role_required(allowed_roles=['provider'])
def providerReviews(request):
    """Provider sees all reviews across their services with average rating."""
    reviews = Review.objects.filter(
        booking__service__provider=request.user
    ).select_related('booking__service', 'booking__resident').order_by('-created_at')

    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']

    return render(request, "service/provider/provider_reviews.html", {
        "reviews": reviews,
        "avg_rating": avg_rating,
    })


# ==========================================================================
#  RESIDENT VIEWS
# ==========================================================================

@role_required(allowed_roles=['resident'])
def listServices(request):
    """Browse services with optional category filter."""
    category_id = request.GET.get('category')
    categories = Category.objects.all()
    services = Service.objects.filter(is_active=True)
    if category_id:
        services = services.filter(category_id=category_id)
    return render(request, "service/resident/services_list.html", {
        "services": services,
        "categories": categories,
        "selected_category": category_id,
    })


@role_required(allowed_roles=['resident'])
def bookService(request, service_id):
    """Resident books a service — now requires POST with scheduled date & notes."""
    service = get_object_or_404(Service, id=service_id, is_active=True)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.service = service
            booking.resident = request.user
            booking.save()

            # Notify provider about new booking
            create_notification(
                user=service.provider,
                message=f'New booking from {request.user.name} for "{service.serviceName}".',
                notification_type='booking',
                link='/service/provider-bookings/',
            )

            return redirect("resident_bookings")
    else:
        form = BookingForm()

    return render(request, "service/resident/book_service.html", {
        "form": form,
        "service": service,
    })


@role_required(allowed_roles=['resident'])
def residentBookings(request):
    bookings = Booking.objects.filter(resident=request.user)
    return render(request, "service/resident/resident_bookings.html", {"bookings": bookings})


@role_required(allowed_roles=['resident'])
def submitReview(request, booking_id):
    """Resident submits a review for a completed booking."""
    booking = get_object_or_404(Booking, id=booking_id, resident=request.user)

    if booking.status != 'completed' or hasattr(booking, 'review'):
        return redirect("resident_bookings")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()

            # Notify provider about new review
            create_notification(
                user=booking.service.provider,
                message=f'{request.user.name} left a {review.rating}★ review for "{booking.service.serviceName}".',
                notification_type='booking',
                link='/service/provider-reviews/',
            )

            return redirect("resident_bookings")
    else:
        form = ReviewForm()

    return render(request, "service/resident/review_form.html", {
        "form": form,
        "booking": booking,
    })


@role_required(allowed_roles=['resident'])
def orderHistory(request):
    """Unified order history: bookings with payment and review info."""
    bookings = Booking.objects.filter(
        resident=request.user
    ).select_related('service', 'service__provider').prefetch_related('payment', 'review').order_by('-booking_date')

    return render(request, "service/resident/order_history.html", {
        "bookings": bookings,
    })


# ==========================================================================
#  TICKET VIEWS (Resident / Provider raise, Support manages)
# ==========================================================================

@role_required(allowed_roles=['resident', 'provider'])
def createTicket(request):
    """Resident or Provider raises a support ticket."""
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.raised_by = request.user
            ticket.save()

            # Notify support team
            from core.models import User as UserModel
            support_users = UserModel.objects.filter(role='support', is_active=True)
            for su in support_users:
                create_notification(
                    user=su,
                    message=f'New ticket raised: "{ticket.subject}" by {request.user.name}.',
                    notification_type='ticket',
                    link='/service/support-tickets/',
                )

            return redirect("my_tickets")
    else:
        form = TicketForm()
    return render(request, "service/tickets/create_ticket.html", {"form": form})


@role_required(allowed_roles=['resident', 'provider'])
def myTickets(request):
    """Users see their own raised tickets."""
    tickets = Ticket.objects.filter(raised_by=request.user)
    return render(request, "service/tickets/my_tickets.html", {"tickets": tickets})


@role_required(allowed_roles=['support'])
def supportTicketList(request):
    """Support team sees all tickets."""
    tickets = Ticket.objects.all()
    return render(request, "service/support/ticket_list.html", {"tickets": tickets})


@role_required(allowed_roles=['support'])
def updateTicketStatus(request, ticket_id, status):
    """Support team updates a ticket's status."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    allowed = ['in_progress', 'resolved', 'closed']
    if status in allowed:
        ticket.status = status
        ticket.assigned_to = request.user
        ticket.save()

        # Notify the ticket raiser
        create_notification(
            user=ticket.raised_by,
            message=f'Your ticket "{ticket.subject}" has been updated to: {status}.',
            notification_type='ticket',
            link='/service/my-tickets/',
        )

    return redirect("support_tickets")


@role_required(allowed_roles=['support'])
def supportQualityMonitor(request):
    """Support dashboard for monitoring provider quality and complaint patterns."""
    from core.models import User as UserModel

    # Providers with avg ratings
    providers = UserModel.objects.filter(role='provider', is_active=True).annotate(
        avg_rating=Avg('services__bookings__review__rating'),
        total_bookings=Count('services__bookings'),
        total_reviews=Count('services__bookings__review'),
    ).order_by('avg_rating')

    # Low-rated reviews (≤ 2 stars)
    low_reviews = Review.objects.filter(rating__lte=2).select_related(
        'booking__service__provider', 'booking__resident'
    ).order_by('-created_at')[:20]

    # Ticket summary by priority
    ticket_stats = {
        'total_open': Ticket.objects.filter(status='open').count(),
        'total_in_progress': Ticket.objects.filter(status='in_progress').count(),
        'high_priority_open': Ticket.objects.filter(status='open', priority='high').count(),
    }

    return render(request, "service/support/quality_monitor.html", {
        "providers": providers,
        "low_reviews": low_reviews,
        "ticket_stats": ticket_stats,
    })


# ==========================================================================
#  ADMIN VIEWS
# ==========================================================================

@role_required(allowed_roles=['admin'])
def adminUserList(request):
    """Admin can see all users."""
    from core.models import User
    users = User.objects.all().order_by('-created_at')
    return render(request, "service/admin/user_list.html", {"users": users})


@role_required(allowed_roles=['admin'])
def adminToggleUser(request, user_id):
    """Admin can activate/deactivate a user."""
    from core.models import User
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()
    return redirect("admin_user_list")


@role_required(allowed_roles=['admin'])
def adminServiceList(request):
    """Admin can see all services."""
    services = Service.objects.all()
    return render(request, "service/admin/service_list.html", {"services": services})


@role_required(allowed_roles=['admin'])
def adminToggleService(request, service_id):
    """Admin can activate/deactivate a service."""
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":
        service.is_active = not service.is_active
        service.save()
    return redirect("admin_service_list")


@role_required(allowed_roles=['admin'])
def adminAnalytics(request):
    """Dashboard with key platform metrics."""
    from core.models import User
    context = {
        "total_users": User.objects.count(),
        "total_providers": User.objects.filter(role='provider').count(),
        "total_residents": User.objects.filter(role='resident').count(),
        "total_services": Service.objects.count(),
        "total_bookings": Booking.objects.count(),
        "completed_bookings": Booking.objects.filter(status='completed').count(),
        "pending_bookings": Booking.objects.filter(status='pending').count(),
        "total_revenue": Booking.objects.filter(status='completed').aggregate(
            total=Sum('service__servicePrize')
        )['total'] or 0,
        "open_tickets": Ticket.objects.filter(status='open').count(),
    }
    return render(request, "service/admin/analytics.html", context)


@role_required(allowed_roles=['admin'])
def adminTicketList(request):
    """Admin can view and manage all support tickets."""
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, "service/admin/admin_ticket_list.html", {"tickets": tickets})


@role_required(allowed_roles=['admin'])
def adminUpdateTicketStatus(request, ticket_id, status):
    """Admin can update any ticket's status."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    allowed = ['in_progress', 'resolved', 'closed']
    if status in allowed:
        ticket.status = status
        ticket.save()

        # Notify the ticket raiser
        create_notification(
            user=ticket.raised_by,
            message=f'Your ticket "{ticket.subject}" has been updated to: {status} by admin.',
            notification_type='ticket',
            link='/service/my-tickets/',
        )

    return redirect("admin_ticket_list")


@role_required(allowed_roles=['admin'])
def adminSettings(request):
    """Admin configures platform settings."""
    settings_obj = SiteSettings.load()

    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect("admin_settings")
    else:
        form = SiteSettingsForm(instance=settings_obj)

    return render(request, "service/admin/site_settings.html", {"form": form})


# ==========================================================================
#  PAYMENT VIEWS
# ==========================================================================

@role_required(allowed_roles=['resident'])
def makePayment(request, booking_id):
    """Initiate Razorpay payment for a completed booking."""
    import razorpay

    booking = get_object_or_404(Booking, id=booking_id, resident=request.user)

    if booking.status != 'completed' or hasattr(booking, 'payment'):
        return redirect("resident_bookings")

    # Amount in paise (Razorpay requires smallest currency unit)
    amount_in_paise = int(booking.service.servicePrize * 100)

    client = razorpay.Client(
        auth=(os.environ.get('RAZORPAY_KEY_ID'), os.environ.get('RAZORPAY_KEY_SECRET'))
    )

    razorpay_order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"booking_{booking.id}",
        "payment_capture": 1,
    })

    return render(request, "service/resident/make_payment.html", {
        "booking": booking,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": os.environ.get('RAZORPAY_KEY_ID'),
        "amount_in_paise": amount_in_paise,
    })


@csrf_exempt
@role_required(allowed_roles=['resident'])
def verifyPayment(request):
    """Verify Razorpay payment signature and record the Payment."""
    import razorpay
    from django.utils import timezone

    if request.method != "POST":
        return redirect("resident_bookings")

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    booking_id = request.POST.get('booking_id')

    booking = get_object_or_404(Booking, id=booking_id, resident=request.user)

    # Verify signature
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '').encode()
    body = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    generated_signature = hmac.new(key_secret, body, hashlib.sha256).hexdigest()

    if generated_signature == razorpay_signature:
        # Payment verified — save the record
        Payment.objects.create(
            booking=booking,
            amount=booking.service.servicePrize,
            status='completed',
            transaction_id=razorpay_payment_id,
            paid_at=timezone.now(),
        )

        create_notification(
            user=booking.service.provider,
            message=f'Payment of ₹{booking.service.servicePrize} received for "{booking.service.serviceName}".',
            notification_type='payment',
            link='/service/provider-earnings/',
        )

        return redirect("payment_success", booking_id=booking.id)
    else:
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect("resident_bookings")


@role_required(allowed_roles=['resident'])
def paymentSuccess(request, booking_id):
    """Show payment confirmation."""
    booking = get_object_or_404(Booking, id=booking_id, resident=request.user)
    payment = get_object_or_404(Payment, booking=booking)
    return render(request, "service/resident/payment_success.html", {
        "booking": booking,
        "payment": payment,
    })


@role_required(allowed_roles=['resident'])
def paymentHistory(request):
    """Resident views all their payments."""
    payments = Payment.objects.filter(booking__resident=request.user).order_by('-created_at')
    return render(request, "service/resident/payment_history.html", {
        "payments": payments,
    })


@role_required(allowed_roles=['admin'])
def adminPayments(request):
    """Admin views all payments on the platform."""
    payments = Payment.objects.all().order_by('-created_at')
    total_revenue = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    return render(request, "service/admin/payments.html", {
        "payments": payments,
        "total_revenue": total_revenue,
    })


# ==========================================================================
#  MESSAGING VIEWS
# ==========================================================================

@role_required(allowed_roles=['resident', 'provider'])
def bookingConversation(request, booking_id):
    """Chat thread between resident and provider on a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.resident and request.user != booking.service.provider:
        return HttpResponseForbidden("You are not part of this booking.")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.booking = booking
            msg.sender = request.user
            msg.save()

            # Notify the other party
            recipient = booking.service.provider if request.user == booking.resident else booking.resident
            create_notification(
                user=recipient,
                message=f'New message from {request.user.name} on booking "{booking.service.serviceName}".',
                notification_type='message',
                link=f'/service/conversation/{booking.id}/',
            )

            return redirect("booking_conversation", booking_id=booking.id)
    else:
        form = MessageForm()

    messages_list = booking.messages.all()
    return render(request, "service/messages/conversation.html", {
        "booking": booking,
        "messages_list": messages_list,
        "form": form,
    })


# ==========================================================================
#  NOTIFICATION VIEWS
# ==========================================================================

def notificationList(request):
    """Show all notifications for the logged-in user."""
    if not request.user.is_authenticated:
        return redirect('login')

    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()

    return render(request, "service/notifications/notification_list.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


def markNotificationRead(request, notification_id):
    """Mark a single notification as read."""
    if not request.user.is_authenticated:
        return redirect('login')

    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if notification.link:
        return redirect(notification.link)
    return redirect("notification_list")


def markAllNotificationsRead(request):
    """Mark all notifications as read for the current user."""
    if not request.user.is_authenticated:
        return redirect('login')

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notification_list")


# ==========================================================================
#  CHATBOT VIEW (Gemini AI — Resident Only)
# ==========================================================================

@role_required(allowed_roles=['resident'])
def chatbotView(request):
    """Page for resident chatbot."""
    return render(request, "service/resident/chatbot.html")


@role_required(allowed_roles=['resident'])
def chatbotApi(request):
    """AJAX endpoint: sends user message to Gemini and returns response."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        from google import genai

        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        # Gather resident's active bookings for context
        active_bookings = Booking.objects.filter(
            resident=request.user
        ).select_related('service', 'service__provider').order_by('-booking_date')[:5]

        booking_context = "\n".join([
            f"- {b.service.serviceName} by {b.service.provider.name} (Status: {b.status}, Price: ₹{b.service.servicePrize})"
            for b in active_bookings
        ]) or "No recent bookings."

        # Build system prompt
        system_prompt = f"""You are Urban Service AI, a friendly and helpful assistant for the Urban Service Platform.

Platform Overview:
- Residents can browse services (Plumbing, Cleaning, Electrical, etc.), book service providers, track booking status, make payments, and leave reviews.
- Booking statuses: Pending → Accepted → In Progress → Completed.
- After completion, residents pay and can then submit a review.
- Residents can raise Support Tickets for any issue.

Current Resident: {request.user.name} ({request.user.email})
Their Recent Bookings:
{booking_context}

Guidelines:
- Be helpful, concise, and friendly.
- Answer questions about the platform, bookings, and payment process.
- If asked something outside the platform scope, politely redirect.
- Do NOT reveal API keys, internal code, or system details.
"""

        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "user", "parts": [{"text": system_prompt + "\n\nResident says: " + user_message}]}
            ]
        )

        reply = response.text
        return JsonResponse({"reply": reply})

    except Exception as e:
        return JsonResponse({"error": f"AI service error: {str(e)}"}, status=500)
