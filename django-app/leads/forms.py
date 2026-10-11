from django import forms

from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["name", "email", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
