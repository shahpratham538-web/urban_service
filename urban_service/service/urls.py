from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # ---------- Provider ----------
    path("create-service/", views.createService, name="create_service"),
    path("edit-service/<int:service_id>/", views.editService, name="edit_service"),
    path("delete-service/<int:service_id>/", views.deleteService, name="delete_service"),
    path("my-services/", views.providerServices, name="provider_services"),
    path("provider-bookings/", views.providerBookings, name="provider_bookings"),
    path("update-booking/<int:booking_id>/<str:status>/", views.updateBookingStatus, name="update_booking_status"),
    path("provider-earnings/", views.providerEarnings, name="provider_earnings"),
    path("availability/", views.manageAvailability, name="manage_availability"),
    path("availability/edit/<int:slot_id>/", views.editAvailability, name="edit_availability"),
    path("availability/delete/<int:slot_id>/", views.deleteAvailability, name="delete_availability"),
    path("provider-reviews/", views.providerReviews, name="provider_reviews"),

    # ---------- Resident ----------
    path("services/", views.listServices, name="list_services"),
    path("book/<int:service_id>/", views.bookService, name="book_service"),
    path("my-bookings/", views.residentBookings, name="resident_bookings"),
    path("review/<int:booking_id>/", views.submitReview, name="submit_review"),
    path("order-history/", views.orderHistory, name="order_history"),

    # ---------- Tickets (Resident + Provider) ----------
    path("create-ticket/", views.createTicket, name="create_ticket"),
    path("my-tickets/", views.myTickets, name="my_tickets"),

    # ---------- Support ----------
    path("support-tickets/", views.supportTicketList, name="support_tickets"),
    path("update-ticket/<int:ticket_id>/<str:status>/", views.updateTicketStatus, name="update_ticket_status"),
    path("quality-monitor/", views.supportQualityMonitor, name="support_quality_monitor"),

    # ---------- Admin ----------
    path("admin-users/", views.adminUserList, name="admin_user_list"),
    path("admin-toggle-user/<int:user_id>/", views.adminToggleUser, name="admin_toggle_user"),
    path("admin-services/", views.adminServiceList, name="admin_service_list"),
    path("admin-toggle-service/<int:service_id>/", views.adminToggleService, name="admin_toggle_service"),
    path("admin-analytics/", views.adminAnalytics, name="admin_analytics"),
    path("admin-payments/", views.adminPayments, name="admin_payments"),
    path("admin-tickets/", views.adminTicketList, name="admin_ticket_list"),
    path("admin-update-ticket/<int:ticket_id>/<str:status>/", views.adminUpdateTicketStatus, name="admin_update_ticket_status"),
    path("admin-settings/", views.adminSettings, name="admin_settings"),

    # ---------- Payments ----------
    path("pay/<int:booking_id>/", views.makePayment, name="make_payment"),
    path("payment-success/<int:booking_id>/", views.paymentSuccess, name="payment_success"),
    path("payment-history/", views.paymentHistory, name="payment_history"),

    # ---------- Messaging ----------
    path("conversation/<int:booking_id>/", views.bookingConversation, name="booking_conversation"),

    # ---------- Notifications ----------
    path("notifications/", views.notificationList, name="notification_list"),
    path("notifications/read/<int:notification_id>/", views.markNotificationRead, name="mark_notification_read"),
    path("notifications/read-all/", views.markAllNotificationsRead, name="mark_all_notifications_read"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)