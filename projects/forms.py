from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'link', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'link': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }