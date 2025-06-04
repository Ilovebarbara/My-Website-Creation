from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import BlogPost, BlogCategory, Project, Tutorial, Comment, Profile, Notification, Like, Share, PostMedia, TwoFactorAuth, LoginAttempt
from .forms import (
    CommentForm, PostForm, ProfileUpdateForm, ProjectForm, TutorialForm,
    PostMediaFormSet, TwoFactorLoginForm, VerificationCodeForm, ResendCodeForm
)
from .two_factor_utils import send_verification_code, verify_code, check_suspicious_activity

def home(request):
    categories = BlogCategory.objects.all()
    featured_posts = BlogPost.objects.filter(featured=True).order_by('-created_at')[:3]
    projects = Project.objects.filter(featured=True).order_by('-created_at')[:3]
    
    # Only show logged-in user's featured tutorials
    if request.user.is_authenticated:
        tutorials = Tutorial.objects.filter(featured=True, author=request.user).order_by('-created_at')[:3]
    else:
        tutorials = Tutorial.objects.none()
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
    if request.user.is_authenticated:
        projects = Project.objects.all().order_by('-created_at')
    else:
        projects = Project.objects.filter(featured=True).order_by('-created_at')
    return render(request, 'project_list.html', {'projects': projects})

def tutorial_list(request):
    if request.user.is_authenticated:
        tutorials = Tutorial.objects.all().order_by('-created_at')
    else:
        tutorials = Tutorial.objects.filter(featured=True).order_by('-created_at')
    return render(request, 'tutorial_list.html', {'tutorials': tutorials})

def search(request):
    query = request.GET.get('q')
    posts = BlogPost.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)) if query else BlogPost.objects.none()
    return render(request, 'search_results.html', {'posts': posts, 'query': query})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Profile will be created by the signal handler
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('home')
            except Exception as e:
                messages.error(request, str(e) or 'An error occurred during registration. Please try again.')
                return render(request, 'register.html', {'form': form})
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
        form = TwoFactorLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = authenticate(username=username, password=password)
                if user is not None:
                    # Check for suspicious activity
                    security_check = check_suspicious_activity(user, request)
                    
                    # Always require 2FA for additional security
                    if settings.TWO_FACTOR_ENABLED:
                        # Store user info in session for 2FA verification
                        request.session['pending_user_id'] = user.id
                        request.session['pending_login'] = True
                          # Send verification code
                        success, message = send_verification_code(user, request, login_attempt=True)
                        if success:
                            messages.success(request, message)
                            return redirect('verify_2fa')
                        else:
                            messages.error(request, message)
                    else:
                        # Direct login if 2FA is disabled
                        Profile.objects.get_or_create(user=user)
                        login(request, user)
                        messages.success(request, f'Welcome back, {username}!')
                        return redirect('dashboard')
                else:
                    messages.error(request, 'Invalid username or password.')
            except Exception as e:
                messages.error(request, 'An error occurred while logging in. Please try again.')
        else:
            messages.error(request, 'Please check your username and password.')
    else:
        form = TwoFactorLoginForm()
    return render(request, 'login.html', {'form': form})

def verify_2fa(request):
    """Handle 2FA verification"""
    if not request.session.get('pending_login'):
        messages.error(request, 'No pending login found. Please log in again.')
        return redirect('login')
    
    pending_user_id = request.session.get('pending_user_id')
    if not pending_user_id:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('verification_code')
            success, message = verify_code(user, code, login_attempt=True)
            
            if success:
                # Clear session data
                del request.session['pending_login']
                del request.session['pending_user_id']
                
                # Complete login
                Profile.objects.get_or_create(user=user)
                login(request, user)
                
                # Log successful login
                LoginAttempt.objects.create(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
                
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, message)
        else:
            messages.error(request, 'Please enter a valid 6-digit code.')
    else:
        form = VerificationCodeForm()
    
    return render(request, 'auth/verify_2fa.html', {
        'form': form,
        'user': user,
        'masked_email': f"{user.email[:2]}***@{user.email.split('@')[1]}"
    })

@require_POST
def resend_2fa_code(request):
    """Resend 2FA verification code"""
    if not request.session.get('pending_login'):
        return JsonResponse({'success': False, 'message': 'No pending login found.'})
    
    pending_user_id = request.session.get('pending_user_id')
    if not pending_user_id:
        return JsonResponse({'success': False, 'message': 'Session expired.'})
    
    try:
        user = User.objects.get(id=pending_user_id)
        success, message = send_verification_code(user, request, login_attempt=True)
        if success:
            return JsonResponse({
                'success': True, 
                'message': message
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': message
            })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    # Ensure user has a profile
    Profile.objects.get_or_create(user=request.user)
    
    # Get user's content
    user_posts = BlogPost.objects.filter(author=request.user).order_by('-created_at')
    user_projects = Project.objects.filter(author=request.user).order_by('-created_at')
    user_tutorials = Tutorial.objects.filter(author=request.user).order_by('-created_at')
    
    # Get total likes on user's posts
    total_likes = Like.objects.filter(post__author=request.user).count()
    
    # Get user's comments
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    # Get total comments on user's posts
    total_comments = Comment.objects.filter(post__author=request.user).count()
    
    # Get unread notifications
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    
    # Get user's profile
    user_profile = request.user.profile

    context = {
        'user_posts': user_posts,
        'user_projects': user_projects,
        'user_tutorials': user_tutorials,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'user_comments': user_comments,
        'notifications': notifications,
        'user_profile': user_profile,
    }
    return render(request, 'dashboard.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        media_formset = PostMediaFormSet(request.POST, request.FILES)
        if form.is_valid() and media_formset.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # Save tagged users
            
            # Handle media uploads
            media_formset.instance = post
            media_formset.save()
            
            messages.success(request, 'Post created successfully!')
            return redirect('dashboard')
    else:
        form = PostForm()
        media_formset = PostMediaFormSet()
    
    return render(request, 'create_post.html', {
        'form': form,
        'media_formset': media_formset,
        'categories': BlogCategory.objects.all(),
    })

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
    messages.success(request, 'Post deleted successfully!')
    return redirect('dashboard')

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

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.author = request.user
            project.save()
            messages.success(request, 'Project created successfully!')
            return redirect('dashboard')
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})

@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk, author=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('dashboard')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'create_project.html', {'form': form, 'editing': True})

@login_required
def create_tutorial(request):
    if request.method == 'POST':
        form = TutorialForm(request.POST)
        if form.is_valid():
            tutorial = form.save(commit=False)
            tutorial.author = request.user
            tutorial.save()
            messages.success(request, 'Tutorial created successfully!')
            return redirect('dashboard')
    else:
        form = TutorialForm()
    return render(request, 'create_tutorial.html', {'form': form})

@login_required
def edit_tutorial(request, pk):
    tutorial = get_object_or_404(Tutorial, pk=pk, author=request.user)
    if request.method == 'POST':
        form = TutorialForm(request.POST, instance=tutorial)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tutorial updated successfully!')
            return redirect('dashboard')
    else:
        form = TutorialForm(instance=tutorial)
    return render(request, 'create_tutorial.html', {'form': form, 'editing': True})

@login_required
@require_POST
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, author=request.user)
    project.delete()
    messages.success(request, 'Project deleted successfully!')
    return redirect('dashboard')

@login_required
@require_POST
def delete_tutorial(request, pk):
    try:
        tutorial = get_object_or_404(Tutorial, pk=pk, author=request.user)
        tutorial.delete()
        messages.success(request, 'Tutorial deleted successfully!')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Error deleting tutorial: {str(e)}')
        return redirect('dashboard')

@staff_member_required
def security_dashboard(request):
    """Security dashboard for admin"""
    # Get login attempts in the last 24 hours
    time_threshold = timezone.now() - timedelta(days=1)
    recent_logins = LoginAttempt.objects.filter(created_at__gte=time_threshold).order_by('-created_at')
    
    # Get 2FA statistics
    total_2fa_codes = TwoFactorAuth.objects.filter(created_at__gte=time_threshold).count()
    verified_2fa_codes = TwoFactorAuth.objects.filter(
        created_at__gte=time_threshold,
        used=True
    ).count()
    
    # Get users with suspicious activity (multiple failed attempts)
    suspicious_users = []
    ip_failure_counts = {}
    
    # Count failed attempts by IP
    for attempt in recent_logins.filter(success=False):
        ip = attempt.ip_address
        if ip in ip_failure_counts:
            ip_failure_counts[ip] += 1
        else:
            ip_failure_counts[ip] = 1
    
    # Find users with high failure rates
    for attempt in recent_logins.filter(success=False):
        if ip_failure_counts.get(attempt.ip_address, 0) >= 3:  # 3 or more failures
            if attempt.user and attempt.user not in suspicious_users:
                suspicious_users.append(attempt.user)
    
    context = {
        'recent_logins': recent_logins,
        'suspicious_users': suspicious_users,
        'total_2fa_codes': total_2fa_codes,
        'verified_2fa_codes': verified_2fa_codes,
        'success_rate': (verified_2fa_codes / total_2fa_codes * 100) if total_2fa_codes > 0 else 0,
        'failed_attempts_count': recent_logins.filter(success=False).count(),
        'successful_attempts_count': recent_logins.filter(success=True).count(),
    }
    
    return render(request, 'admin/security_dashboard.html', context)
