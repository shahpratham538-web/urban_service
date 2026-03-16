from django import forms
from .models import Service, Review, Booking, Ticket, ProviderAvailability, Message


class ServiceCreationForm(forms.ModelForm):
    """Form used by providers to create / edit a service."""

    class Meta:
        model = Service
        exclude = ['provider']
        widgets = {
            'serviceDescription': forms.Textarea(attrs={'rows': 4}),
        }


class ReviewForm(forms.ModelForm):
    """Residents fill this after a booking is completed."""

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class BookingForm(forms.ModelForm):
    """Used when a resident books a service (picks date & adds notes)."""

    class Meta:
        model = Booking
        fields = ['scheduled_date', 'notes']
        widgets = {
            'scheduled_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class TicketForm(forms.ModelForm):
    """Residents or providers can raise a support ticket."""

    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'priority', 'booking']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class AvailabilityForm(forms.ModelForm):
    """Provider sets their working hours per day."""

    class Meta:
        model = ProviderAvailability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class MessageForm(forms.ModelForm):
    """Send a message in a booking conversation."""

    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'}),
        }