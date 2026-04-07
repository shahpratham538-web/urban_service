from django.shortcuts import render, redirect
from .forms import UserSignupForm, UserLoginForm
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from .decorators import role_required
from django.contrib.auth import logout
from service.models import Booking

def homeView(request):
    """Landing page for the Urban Service Platform."""
    return render(request, 'core/home.html')

def userSignupView(request):

    if request.method == "POST":
        form = UserSignupForm(request.POST or None)

        if form.is_valid():

            # send welcome email
            email = form.cleaned_data['email']

            send_mail(
                subject="Welcome to Urban Service Platform",
                message="Thank you for registering with Urban Service Platform.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )

            form.save()

            return redirect('login')

        else:
            return render(request, 'core/signup.html', {'form': form})

    else:
        form = UserSignupForm()
        return render(request, 'core/signup.html', {'form': form})

def userLoginView(request):

    if request.method == "POST":
        form = UserLoginForm(request.POST or None)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)

            if user:
                login(request, user)

                if user.role == "provider":
                    return redirect("provider_dashboard")

                elif user.role == "resident":
                    return redirect("resident_dashboard")

                elif user.role == "admin":
                    return redirect("admin_dashboard")

                elif user.role == "support":
                    return redirect("support_dashboard")

            else:
                return render(request, "core/login.html", {"form": form})

        # IMPORTANT: if form is invalid
        return render(request, "core/login.html", {"form": form})

    else:
        form = UserLoginForm()

    return render(request, "core/login.html", {"form": form})

@role_required(allowed_roles=['admin'])
def adminDashboardView(request):
    return render(request,"urban_service/admin/admin_dashboard.html")


@role_required(allowed_roles=['provider'])
def providerDashboardView(request):
    return render(request,"urban_service/provider/provider_dashboard.html")


@role_required(allowed_roles=['resident'])
def residentDashboardView(request):
    # Bookings that are completed by the provider but not yet paid by the resident
    pending_payments = Booking.objects.filter(
        resident=request.user,
        status='completed',
        payment__isnull=True,
    ).select_related('service', 'service__provider')

    return render(request, "urban_service/resident/resident_dashboard.html", {
        "pending_payments": pending_payments,
    })


@role_required(allowed_roles=['support'])
def supportDashboardView(request):
    return render(request,"urban_service/support/support_dashboard.html")

def userLogoutView(request):
    logout(request)
    return redirect("login")