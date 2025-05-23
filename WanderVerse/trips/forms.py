from django import forms
from django.core.exceptions import ValidationError
from datetime import date

class TripForm(forms.Form):
    city = forms.CharField(label='City', max_length=100)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # Check if start date is in the past
            if start_date < date.today():
                raise ValidationError("Start date cannot be in the past")
            
            # Check if end date is before start date
            if end_date < start_date:
                raise ValidationError("End date must be after start date")

        return cleaned_data
