from django import forms

class TripForm(forms.Form):
    city = forms.CharField(label='City', max_length=100)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
