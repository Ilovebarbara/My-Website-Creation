from django import forms
from django.utils.text import slugify
from .models import BlogPost, Comment, Profile

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'category']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Write your post content here...'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select a category'
            })
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            slug = slugify(instance.title)
            count = 0
            while BlogPost.objects.filter(slug=slug).exists():
                count += 1
                slug = f"{slugify(instance.title)}-{count}"
            instance.slug = slug
        
        if commit:
            instance.save()
        return instance

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write something about yourself...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
