from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

# Create your models here.

class BlogCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji or icon for category")

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private')
    ]
    FEELING_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('excited', 'Excited'),
        ('tired', 'Tired'),
        ('loved', 'Loved'),
        ('angry', 'Angry')
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    shares = models.ManyToManyField(User, related_name='shared_posts', blank=True)
    
    # New fields
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    location = models.CharField(max_length=100, blank=True)
    feeling = models.CharField(max_length=10, choices=FEELING_CHOICES, blank=True)
    activity = models.CharField(max_length=100, blank=True)
    tagged_users = models.ManyToManyField(User, related_name='tagged_posts', blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', null=True)  # Temporarily allow null

    def __str__(self):
        return self.title

class Tutorial(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutorials')
    created_at = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def get_absolute_url(self):
        return reverse('tutorial_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')

class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')

class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.sender.username} {self.notification_type} notification for {self.recipient.username}'

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name}"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class PostMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video')
    ]
    
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='post_media/')
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.media_type} for {self.post.title}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create or update Profile instance for the User."""
    Profile.objects.get_or_create(user=instance)
