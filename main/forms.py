from django import forms
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import BlogPost, Comment, Profile, Project, Tutorial, PostMedia

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

class PostMediaFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_size = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                file = form.cleaned_data.get('file', None)
                if file:
                    total_size += file.size
                    # 10MB limit per file
                    if file.size > 10 * 1024 * 1024:
                        raise forms.ValidationError("Each file must be less than 10MB")
        # 50MB total limit
        if total_size > 50 * 1024 * 1024:
            raise forms.ValidationError("Total upload size cannot exceed 50MB")

class PostMediaForm(forms.ModelForm):
    class Meta:
        model = PostMedia
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("File size must be less than 10MB")
            if not file.content_type.startswith(('image/', 'video/')):
                raise forms.ValidationError("Only image and video files are allowed")
        return file

PostMediaFormSet = forms.inlineformset_factory(
    BlogPost, 
    PostMedia, 
    form=PostMediaForm,
    formset=PostMediaFormSet,
    extra=1,
    max_num=10,
    can_delete=True
)

class PostForm(forms.ModelForm):
    tagged_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-placeholder': 'Tag people in your post...'
        })
    )
    
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'category', 'privacy', 'location', 'feeling', 'activity', 'tagged_users']
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
            }),
            'privacy': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Add location...',
                'id': 'location-input'
            }),
            'feeling': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What are you doing?'
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

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'link', 'featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your project...'
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Project URL (optional)'
            }),
            'featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class TutorialForm(forms.ModelForm):
    class Meta:
        model = Tutorial
        fields = ['title', 'content', 'difficulty_level', 'featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tutorial title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your tutorial content here...'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class TwoFactorLoginForm(AuthenticationForm):
    """Enhanced login form that supports 2FA"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

class VerificationCodeForm(forms.Form):
    """Form for entering 2FA verification code"""
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'style': 'font-size: 24px; letter-spacing: 8px; font-weight: bold;',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric'
        }),
        help_text='Enter the 6-digit code sent to your email'
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        if code and not code.isdigit():
            raise forms.ValidationError('Verification code must contain only numbers.')
        return code

class ResendCodeForm(forms.Form):
    """Form for resending verification code"""
    pass
