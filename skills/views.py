from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from .models import UserProfile, ServicePost, ServiceRequest, Message, Review
from .forms import UserRegisterForm, UserProfileForm, ServicePostForm, ServiceRequestForm, MessageForm, ReviewForm

def home(request):
    category = request.GET.get('category')
    services = ServicePost.objects.all()
    if category:
        services = services.filter(category=category)
    
    context = {
        'services': services,
        'category': category,
        'categories': ServicePost.CATEGORY_CHOICES
    }
    return render(request, 'home.html', context)

def requests_hub(request):
    category = request.GET.get('category')
    reqs = ServiceRequest.objects.filter(is_active=True)
    if category:
        reqs = reqs.filter(category=category)
    
    context = {
        'requests': reqs,
        'category': category,
        'categories': ServicePost.CATEGORY_CHOICES
    }
    return render(request, 'requests.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    user_services = ServicePost.objects.filter(author=profile.user)
    return render(request, 'profile.html', {
        'profile': profile,
        'user_services': user_services
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user.profile)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def post_service(request):
    if request.method == 'POST':
        form = ServicePostForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.author = request.user
            service.save()
            messages.success(request, 'Service posted successfully!')
            return redirect('home')
    else:
        form = ServicePostForm()
    return render(request, 'post_service.html', {'form': form})

@login_required
def post_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.requester = request.user
            req.save()
            messages.success(request, 'Request posted successfully!')
            return redirect('requests_hub')
    else:
        form = ServiceRequestForm()
    return render(request, 'post_request.html', {'form': form})

def service_detail(request, pk):
    service = get_object_or_404(ServicePost, pk=pk)
    reviews = service.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    message_form = MessageForm()
    review_form = ReviewForm()
    
    if request.method == 'POST':
        if 'send_message' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            m_form = MessageForm(request.POST)
            if m_form.is_valid():
                msg = m_form.save(commit=False)
                msg.sender = request.user
                msg.recipient = service.author
                msg.save()
                messages.success(request, 'Message sent!')
                return redirect('service_detail', pk=pk)
        
        elif 'add_review' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            r_form = ReviewForm(request.POST)
            if r_form.is_valid():
                rev = r_form.save(commit=False)
                rev.author = request.user
                rev.service = service
                rev.save()
                messages.success(request, 'Review added!')
                return redirect('service_detail', pk=pk)

    context = {
        'service': service,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'message_form': message_form,
        'review_form': review_form
    }
    return render(request, 'service_detail.html', context)

@login_required
def inbox(request):
    received_messages = Message.objects.filter(recipient=request.user)
    return render(request, 'inbox.html', {'received_messages': received_messages})

def search(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    results_services = ServicePost.objects.all()
    results_requests = ServiceRequest.objects.all()
    
    if query:
        results_services = results_services.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )
        results_requests = results_requests.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        
    if category:
        results_services = results_services.filter(category=category)
        results_requests = results_requests.filter(category=category)
        
    context = {
        'query': query,
        'results_services': results_services,
        'results_requests': results_requests,
        'categories': ServicePost.CATEGORY_CHOICES,
        'selected_category': category
    }
    return render(request, 'search_results.html', context)

@login_required
def my_services(request):
    user_services = ServicePost.objects.filter(author=request.user)
    user_requests = ServiceRequest.objects.filter(requester=request.user)
    return render(request, 'my_services.html', {
        'user_services': user_services,
        'user_requests': user_requests
    })

@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServicePost, pk=pk, author=request.user)
    service.delete()
    messages.success(request, 'Post deleted.')
    return redirect('my_services')
