from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import json
from .models import UserProfile, Service, HelpRequest, Message, Review, Request, CATEGORY_CHOICES, Payment, Notification
from .forms import UserRegisterForm, UserProfileForm, ServiceForm, HelpRequestForm, MessageForm, ReviewForm, RequestForm


def home(request):
    category = request.GET.get('category')
    services = Service.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('-created_at')
    
    if category:
        services = services.filter(category=category)
        
    # --- AI RECOMMENDATION LOGIC ---
    recommended_services = []
    if request.user.is_authenticated:
        user_profile = getattr(request.user, 'profile', None)
        if user_profile and user_profile.skills_offered:
            # Recommend services that complement their skills or are highly rated
            user_skills = [s.strip().lower() for s in user_profile.skills_offered.split(',')]
            recommended_services = Service.objects.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=4.0).exclude(user=request.user).order_by('-avg_rating')[:4]
            
        if not recommended_services:
            # Fallback based on location
            if user_profile and user_profile.location:
                recommended_services = Service.objects.annotate(
                    avg_rating=Avg('reviews__rating')
                ).filter(location__icontains=user_profile.location).exclude(user=request.user)[:4]

    context = {
        'services': services,
        'category': category,
        'categories': CATEGORY_CHOICES,
        'recommended_services': recommended_services
    }
    return render(request, 'home.html', context)

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        messages.success(request, f'Thank you for your message, {name}! We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')

def requests_hub(request):
    category = request.GET.get('category')
    reqs = HelpRequest.objects.filter(is_active=True)
    if category:
        reqs = reqs.filter(category=category)
    
    context = {
        'requests': reqs,
        'category': category,
        'categories': CATEGORY_CHOICES,
    }
    return render(request, 'requests.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Account created for {username}! You can now log in.')
                return redirect('login')
            except Exception as e:
                # Handle database-level duplicates that escaped form validation (e.g. case sensitivity)
                if 'UNIQUE constraint failed: auth_user.username' in str(e):
                    form.add_error('username', 'A user with that username already exists.')
                else:
                    form.add_error(None, f'An unexpected error occurred: {e}')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def profile_view(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    user_services = Service.objects.filter(user=profile.user)
    
    # New Data for Modern Profile
    reviews = Review.objects.filter(service__user=profile.user).order_by('-created_at')
    activity = Request.objects.filter(
        Q(sender=profile.user) | Q(receiver=profile.user)
    ).select_related('service', 'sender', 'receiver').order_by('-created_at')[:10]
    
    completed_requests = Request.objects.filter(receiver=profile.user, status='completed').count()
    earnings = Payment.objects.filter(
        service__user=profile.user, 
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'profile': profile,
        'user_services': user_services,
        'reviews': reviews,
        'activity': activity,
        'completed_requests': completed_requests,
        'earnings': earnings
    }
    return render(request, 'profile.html', context)

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
        form = ServiceForm(request.POST, request.FILES)

        if form.is_valid():
            service = form.save(commit=False)
            service.user = request.user
            print(f"DEBUG: Saving service '{service.title}' with payment_type: {service.payment_type}")
            service.save()
            messages.success(request, 'Service posted successfully!')
            return redirect('home')
    else:
        form = ServiceForm()
    return render(request, 'post_service.html', {'form': form})

@login_required
def post_request(request):
    if request.method == 'POST':
        form = HelpRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, 'Request posted successfully!')
            return redirect('requests_hub')
    else:
        form = HelpRequestForm()
    return render(request, 'post_request.html', {'form': form})

def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    reviews = service.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    booking_form = RequestForm()
    review_form = ReviewForm()
    
    # Check if a booking already exists
    user_booking = None
    if request.user.is_authenticated:
        user_booking = Request.objects.filter(service=service, sender=request.user).exclude(status='rejected').last() if request.user.is_authenticated else None
    
    # Check if user can review (must have a completed request AND hasn't reviewed yet)
    can_review = False
    if request.user.is_authenticated:
        has_completed = Request.objects.filter(service=service, sender=request.user, status='completed').exists()
        has_reviewed = Review.objects.filter(user=request.user, service=service).exists()
        can_review = has_completed and not has_reviewed

    if request.method == 'POST':
        if 'request_service' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            b_form = RequestForm(request.POST)
            if b_form.is_valid():
                target_service = service  # Use the 'service' object already fetched
                sender_user = request.user
                receiver_user = target_service.user

                if sender_user == receiver_user:
                    messages.error(request, "You cannot request your own service.")
                    return redirect('service_detail', pk=pk)

                # Direct creation as requested to ensure data integrity
                Request.objects.create(
                    sender=sender_user,
                    receiver=receiver_user,
                    service=target_service,
                    message=b_form.cleaned_data.get('message', ''),
                    status='pending'
                )
                
                messages.success(request, f'Service request sent successfully to {receiver_user.username}!')
                return redirect('inbox')
        
        elif 'add_review' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            
            if Review.objects.filter(user=request.user, service=service).exists():
                messages.error(request, 'You have already reviewed this service.')
                return redirect('service_detail', pk=pk)
                
            r_form = ReviewForm(request.POST)
            if r_form.is_valid():
                rev = r_form.save(commit=False)
                rev.user = request.user
                rev.service = service
                rev.save()
                messages.success(request, 'Review added!')
                return redirect('service_detail', pk=pk)

    context = {
        'service': service,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'booking_form': booking_form,
        'review_form': review_form,
        'user_booking': user_booking,
        'can_review': can_review
    }
    return render(request, 'service_detail.html', context)

@login_required
def booking_inbox(request):
    return redirect('inbox')

@login_required
def accept_request(request, id):
    # Using Request model
    req = get_object_or_404(Request, id=id, receiver=request.user)
    req.status = 'accepted'
    req.save()
    messages.success(request, 'Request accepted successfully!')
    return redirect('inbox')

@login_required
def complete_request(request, id):
    booking = get_object_or_404(Request, id=id)
    # Only the sender (seeker) can mark it as completed
    if booking.sender == request.user:
        booking.status = 'completed'
        booking.save()
        messages.success(request, f"Service '{booking.service.title}' marked as completed! You can now leave a review.")
    else:
        messages.error(request, "Permission denied.")
    return redirect('inbox')

@login_required
def reject_request(request, id):
    # Using Request model
    req = get_object_or_404(Request, id=id, receiver=request.user)
    req.status = 'rejected'
    req.save()
    messages.warning(request, 'Request rejected.')
    return redirect('inbox')

@login_required
def add_meeting_link(request, id):
    req = get_object_or_404(Request, id=id, receiver=request.user)
    if req.status in ['accepted', 'paid']:
        if request.method == 'POST':
            link = request.POST.get('meeting_link')
            if link:
                req.meeting_link = link
                req.save()
                messages.success(request, 'Meeting link added successfully!')
            else:
                messages.error(request, 'Meeting link cannot be empty.')
    else:
        messages.error(request, 'You cannot add a meeting link at this stage.')
    return redirect('inbox')
@login_required
def send_message_inbox(request, request_id):
    booking = get_object_or_404(Request, id=request_id)
    
    if booking.status in ['rejected', 'completed']:
        messages.error(request, "Communication is closed for this inquiry.")
        return redirect('inbox')
        
    if request.method == 'POST':
        message_text = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        if attachment:
            if request.user == booking.sender:
                booking.requirement_file = attachment
                messages.success(request, 'Requirement file uploaded!')
            elif request.user == booking.receiver:
                booking.delivery_file = attachment
                messages.success(request, 'Delivery file uploaded!')
            booking.save()
            
        if message_text:
            if request.user == booking.sender:
                receiver = booking.receiver
            else:
                receiver = booking.sender
                
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                request=booking,
                message=message_text
            )
            messages.success(request, 'Message sent!')
    return redirect('inbox')

@login_required
def manage_booking(request, pk, action):
    # Keeping for compatibility if needed, but redirects to the new clean views
    if action == 'accept':
        return accept_request(request, pk)
    elif action == 'reject':
        return reject_request(request, pk)
    return redirect('booking_inbox')

@login_required
def inbox(request):
    # Mark user's notifications as read when they open the inbox
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # Requirement: Fetch requests where user is either Sender OR Receiver
    requests = Request.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('service', 'sender', 'receiver').order_by('-created_at')
    
    # Pass to template as 'requests'
    return render(request, 'inbox.html', {
        'requests': requests
    })

@login_required
def sent_messages(request):
    return redirect('inbox')

def search(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    max_price = request.GET.get('max_price', '')
    
    results_services = Service.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('-created_at')
    results_requests = HelpRequest.objects.all()
    
    if query:
        results_services = results_services.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        results_requests = results_requests.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        
    if category:
        results_services = results_services.filter(category=category)
        results_requests = results_requests.filter(category=category)

    if location:
        results_services = results_services.filter(location__icontains=location)
        
    if max_price and max_price.isdigit():
        results_services = results_services.filter(price__lte=max_price)
        
    context = {
        'query': query,
        'location': location,
        'max_price': max_price,
        'results_services': results_services,
        'results_requests': results_requests,
        'categories': CATEGORY_CHOICES,
        'selected_category': category
    }
    return render(request, 'search_results.html', context)

@login_required
def dashboard(request):
    user_services = Service.objects.filter(user=request.user)
    user_requests = HelpRequest.objects.filter(user=request.user)
    
    # New calculated stats for modern dashboard
    total_services = user_services.count()
    total_requests = user_requests.count()
    pending_actions = Request.objects.filter(receiver=request.user, status='pending').count()
    
    # TOTAL Earnings: Sum of successful payments made for services OWNED by the current user
    total_earnings = Payment.objects.filter(
        service__user=request.user, 
        status='success'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    # Pictorial stats calculations
    accepted_requests = Request.objects.filter(receiver=request.user, status='accepted').count()
    
    # Percentage logic (clamping between 0 and 100)
    def calc_percent(value, target):
        if not target: return 0
        return min(100, int((value / target) * 100))
    
    # Targets (Defaults)
    service_target = 10
    request_target = 20
    earnings_goal = 5000
    
    services_percent = calc_percent(total_services, service_target)
    requests_percent = calc_percent(total_requests, request_target)
    acceptance_rate = calc_percent(accepted_requests, total_requests) if total_requests else 0
    earnings_percent = calc_percent(total_earnings, earnings_goal)
    seven_days_ago = timezone.now().date() - timedelta(days=6)
    daily_requests = Request.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        created_at__date__gte=seven_days_ago
    ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
    
    # Fill gaps in 7-day data
    date_labels = []
    date_counts = []
    for i in range(7):
        curr_date = seven_days_ago + timedelta(days=i)
        date_labels.append(curr_date.strftime("%b %d"))
        count = next((item['count'] for item in daily_requests if item['date'] == curr_date), 0)
        date_counts.append(count)
        
    # --- CHART DATA 2: Services By Category ---
    category_data = user_services.values('category').annotate(count=Count('id')).order_by('-count')
    category_labels = [dict(CATEGORY_CHOICES).get(item['category'], item['category']) for item in category_data]
    category_counts = [item['count'] for item in category_data]

    # --- RECENT ACTIVITY LEDGER ---
    # Latest unified requests for dashboard
    recent_requests = Request.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('service', 'sender', 'receiver').order_by('-created_at')[:5]
    
    # Latest messages
    recent_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'request').order_by('-timestamp')[:5]
    
    # Latest payments
    latest_payments = Payment.objects.filter(
        Q(user=request.user) | Q(service__user=request.user)
    ).select_related('user', 'service').order_by('-timestamp')[:5]
    
    received_messages = Message.objects.filter(receiver=request.user)[:5]
    sent_messages = Message.objects.filter(sender=request.user)[:5]
    
    return render(request, 'dashboard.html', {
        'user_services': user_services,
        'user_requests': user_requests,
        'total_services': total_services,
        'total_requests': total_requests,
        'pending_actions': pending_actions,
        'total_earnings': total_earnings,
        'accepted_requests': accepted_requests,
        'services_percent': services_percent,
        'requests_percent': requests_percent,
        'acceptance_rate': acceptance_rate,
        'earnings_percent': earnings_percent,
        'recent_requests': recent_requests,
        'recent_messages': recent_messages, # Added unified messages
        'latest_payments': latest_payments,
        'chart_labels': json.dumps(date_labels),
        'chart_data': json.dumps(date_counts),
        'cat_labels': json.dumps(category_labels),
        'cat_data': json.dumps(category_counts),
        'received_messages': received_messages,
        'sent_messages': sent_messages,
    })

@login_required
def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk, user=request.user)
    service.delete()
    messages.success(request, 'Post deleted.')
    return redirect('dashboard')
@login_required
def payment_view(request, service_id):
    """Legacy view kept for backward compatibility (from service_detail page)."""
    service = get_object_or_404(Service, pk=service_id)
    amount = service.price if service.price else 0

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        payment = Payment.objects.create(
            user=request.user,
            service=service,
            amount=amount,
            payment_method=payment_method,
            status='success'
        )
        if service.user and request.user != service.user:
            Request.objects.create(
                sender=request.user,
                receiver=service.user,
                service=service,
                message=f"AUTOGENERATED: Payment of ₹{amount} confirmed via {payment_method.upper()}.",
                status='paid',
                payment=payment
            )
            Message.objects.create(
                sender=request.user,
                receiver=service.user,
                service=service,
                message=f"Payment for '{service.title}' completed. Ref: #SKL{payment.pk+10000}."
            )
            messages.success(request, f'Payment of ₹{amount} successful!')
        return redirect('payment_success', payment_id=payment.pk)

    return render(request, 'payment.html', {'service': service, 'amount': amount})


@login_required
def payment_from_request(request, request_id):
    """
    New view: payment triggered from inbox after a request is ACCEPTED.
    Enforces all payment guards from the requirements.
    """
    booking = get_object_or_404(Request, pk=request_id)

    # GUARD 1: Only the requester (sender) can pay
    if request.user != booking.sender:
        messages.error(request, "Only the requester can make a payment.")
        return redirect('inbox')

    # GUARD 2: Payment only allowed after acceptance
    if booking.status != 'accepted':
        return redirect('inbox')

    # GUARD 3: No duplicate payments
    if hasattr(booking, 'request_payment') and booking.request_payment is not None:
        messages.warning(request, "Payment has already been completed for this request.")
        return redirect('payment_success', payment_id=booking.request_payment.pk)

    service = booking.service
    amount = service.price if service.price else 0

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect('payment_from_request', request_id=request_id)

        # Create the Payment record linked to the Request
        payment = Payment.objects.create(
            user=request.user,
            service=service,
            request=booking,
            amount=amount,
            payment_method=payment_method,
            status='success'
        )

        # Update request status to 'paid'
        booking.status = 'paid'
        booking.save()

        # Send confirmation message to service provider
        Message.objects.create(
            sender=request.user,
            receiver=booking.receiver,
            request=booking,
            message=(
                f"Payment of ₹{amount} for '{service.title}' completed via "
                f"{payment_method.upper()}. Ref: #SKL{payment.pk + 10000}."
            )
        )

        messages.success(request, f'Payment of ₹{amount} successful! Booking confirmed.')
        return redirect('payment_success', payment_id=payment.pk)

    return render(request, 'payment.html', {
        'service': service,
        'amount': amount,
        'booking': booking,
    })

@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)
    return render(request, 'payment_success.html', {'payment': payment})

# --- AJAX CHAT SYSTEM ---
@login_required
def fetch_new_messages(request, request_id):
    booking = get_object_or_404(Request, pk=request_id)
    if request.user != booking.sender and request.user != booking.receiver:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    messages = Message.objects.filter(request=booking).order_by('timestamp')
    data = []
    for m in messages:
        # Mark as read if user is receiver
        if m.receiver == request.user and not m.is_read:
            m.is_read = True
            m.save()
            
        data.append({
            'id': m.id,
            'sender': m.sender.username,
            'receiver': m.receiver.username,
            'message': m.message,
            'timestamp': m.timestamp.strftime("%b %d, %Y, %I:%M %p"),
            'is_read': m.is_read,
            'is_current_user': m.sender == request.user
        })
    return JsonResponse({'messages': data})

# --- ADMIN DASHBOARD ---
@staff_member_required
def admin_panel(request):
    users_count = User.objects.count()
    services_count = Service.objects.count()
    requests_count = Request.objects.count()
    
    total_revenue = Payment.objects.filter(status='success').aggregate(Sum('amount'))['amount__sum'] or 0
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_payments = Payment.objects.filter(status='success').order_by('-timestamp')[:5]
    
    context = {
        'users_count': users_count,
        'services_count': services_count,
        'requests_count': requests_count,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
        'recent_payments': recent_payments,
    }
    return render(request, 'admin_dashboard.html', context)

