from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import BlogPost, BlogCategory, Project, Tutorial, Comment, Profile, Notification, Like, Share
from .forms import CommentForm, PostForm, ProfileUpdateForm

def home(request):
    categories = BlogCategory.objects.all()
    featured_posts = BlogPost.objects.filter(featured=True).order_by('-created_at')[:3]
    projects = Project.objects.filter(featured=True).order_by('-created_at')[:3]
    tutorials = Tutorial.objects.filter(featured=True).order_by('-created_at')[:3]
    return render(request, 'home.html', {
        'categories': categories,
        'featured_posts': featured_posts,
        'projects': projects,
        'tutorials': tutorials,
    })

def blog_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')
    posts = BlogPost.objects.all().order_by('-created_at')
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if category:
        posts = posts.filter(category__name=category)
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = BlogCategory.objects.all()
    return render(request, 'blog_list.html', {'page_obj': page_obj, 'categories': categories})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    comments = post.comments.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('blog_detail', slug=slug)
    else:
        form = CommentForm()
    return render(request, 'blog_detail.html', {'post': post, 'comments': comments, 'form': form})

def project_list(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'project_list.html', {'projects': projects})

def tutorial_list(request):
    tutorials = Tutorial.objects.all().order_by('-created_at')
    return render(request, 'tutorial_list.html', {'tutorials': tutorials})

def search(request):
    query = request.GET.get('q')
    posts = BlogPost.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)) if query else BlogPost.objects.none()
    return render(request, 'search_results.html', {'posts': posts, 'query': query})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)  # Create profile for new user
            login(request, user)
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    # Get user's posts
    user_posts = BlogPost.objects.filter(author=request.user).order_by('-created_at')
    print("DEBUG: user_posts:", user_posts)  # Debug statement
    
    # Get total likes on user's posts
    total_likes = Like.objects.filter(post__author=request.user).count()
    
    # Get user's comments
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    # Get total comments on user's posts
    total_comments = Comment.objects.filter(post__author=request.user).count()
    
    # Get unread notifications
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    
    # Get featured projects and tutorials
    featured_projects = Project.objects.filter(featured=True)[:3]
    featured_tutorials = Tutorial.objects.filter(featured=True)[:3]
    
    # Get user's profile
    user_profile = request.user.profile

    context = {
        'user_posts': user_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'user_comments': user_comments,
        'notifications': notifications,
        'user_projects': featured_projects,
        'user_tutorials': featured_tutorials,
        'user_profile': user_profile,  # Add profile to context
    }
    return render(request, 'dashboard.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('dashboard')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

@login_required
def edit_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('dashboard')
    else:
        form = PostForm(instance=post)
    return render(request, 'create_post.html', {'form': form, 'editing': True})

@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, author=request.user)
    post.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def toggle_featured(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, author=request.user)
    post.featured = not post.featured
    post.save()
    return JsonResponse({
        'status': 'success',
        'featured': post.featured
    })

@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(BlogPost, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
        
    return JsonResponse({
        'status': 'success',
        'likes_count': post.likes.count(),
        'is_liked': created
    })

@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    content = request.POST.get('content')
    
    if content:
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        return JsonResponse({
            'status': 'success',
            'author': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%B %d, %Y %H:%M')
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def notifications(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    unread = notifications.filter(is_read=False)
    
    # Mark notifications as read
    unread.update(is_read=True)
    
    return render(request, 'notifications.html', {
        'notifications': notifications
    })

@login_required
@require_POST
def follow_toggle(request):
    user_to_follow = get_object_or_404(User, id=request.POST.get('user_id'))
    user_profile = request.user.profile
    
    if user_to_follow == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself'}, status=400)
    
    if user_profile.following.filter(id=user_to_follow.profile.id).exists():
        user_profile.following.remove(user_to_follow.profile)
        is_following = False
    else:
        user_profile.following.add(user_to_follow.profile)
        is_following = True
        
        # Create notification
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow'
        )
    
    return JsonResponse({
        'status': 'success',
        'is_following': is_following,
        'followers_count': user_to_follow.profile.followers.count()
    })

@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    
    # Ensure profile exists
    Profile.objects.get_or_create(user=user)
    
    posts = BlogPost.objects.filter(author=user).order_by('-created_at')
    is_following = request.user.is_authenticated and request.user.profile.following.filter(user=user).exists()
    
    context = {
        'profile_user': user,
        'posts': posts,
        'is_own_profile': user == request.user,
        'post_count': posts.count(),
        'followers_count': user.profile.followers.count(),
        'following_count': user.profile.following.count(),
        'is_following': is_following,
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    # Ensure profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'edit_profile.html', {'form': form})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
        
    return render(request, 'contact.html')
