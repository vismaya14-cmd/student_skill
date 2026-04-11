from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from .models import UserProfile, ServicePost, ServiceRequest, Message, Review, ServiceBooking, CATEGORY_CHOICES, Payment
from .forms import UserRegisterForm, UserProfileForm, ServicePostForm, ServiceRequestForm, MessageForm, ReviewForm, ServiceBookingForm


def home(request):
    category = request.GET.get('category')
    services = ServicePost.objects.all()
    if category:
        services = services.filter(category=category)
    
    context = {
        'services': services,
        'category': category,
        'categories': CATEGORY_CHOICES

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
        'categories': CATEGORY_CHOICES,
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
        form = ServicePostForm(request.POST, request.FILES)

        if form.is_valid():
            service = form.save(commit=False)
            service.author = request.user
            print(f"DEBUG: Saving service '{service.title}' with payment_type: {service.payment_type}")
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
    
    booking_form = ServiceBookingForm()
    review_form = ReviewForm()
    
    # Check if a booking already exists
    user_booking = None
    if request.user.is_authenticated:
        user_booking = ServiceBooking.objects.filter(sender=request.user, service=service).first()
    
    if request.method == 'POST':
        if 'request_service' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            b_form = ServiceBookingForm(request.POST)
            if b_form.is_valid():
                # Ensure the user isn't requesting their own service
                if request.user == service.author:
                    messages.error(request, "You cannot request your own service.")
                    return redirect('service_detail', pk=pk)
                
                booking = b_form.save(commit=False)
                booking.sender = request.user
                booking.receiver = service.author
                booking.service = service
                
                # DEBUG LOGGING
                print(f"--- DEBUG: MANUAL REQUEST ---")
                print(f"Sender: {booking.sender.username}")
                print(f"Receiver (Owner): {booking.receiver.username if booking.receiver else 'NULL'}")
                print(f"Service: {booking.service.title}")
                print(f"-----------------------------")

                if booking.receiver:
                    booking.save()
                    messages.success(request, f'Service request sent successfully to {service.author.username}!')
                else:
                    messages.error(request, 'Error: Service provider not found.')
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
        'booking_form': booking_form,
        'review_form': review_form,
        'user_booking': user_booking
    }
    return render(request, 'service_detail.html', context)

@login_required
def booking_inbox(request):
    # Fetch private service bookings (Receiver = You)
    received_bookings = ServiceBooking.objects.filter(receiver=request.user)
    
    # Fetch private service bookings (Sender = You)
    sent_bookings = ServiceBooking.objects.filter(sender=request.user)
    
    # Fetch public help-requests you've posted
    user_requests = ServiceRequest.objects.filter(requester=request.user)
    
    # Unify for the 'Requests' context variable as requested
    requests = list(received_bookings)
    
    return render(request, 'booking_inbox.html', {
        'received_bookings': received_bookings,
        'sent_bookings': sent_bookings,
        'user_requests': user_requests,
        'requests': requests # Mapping the loop variable
    })

@login_required
def accept_request(request, id):
    # Using ServiceBooking as the 'Request' model for this project
    req = get_object_or_404(ServiceBooking, id=id, receiver=request.user)
    req.status = 'accepted'
    req.save()
    messages.success(request, 'Request accepted successfully!')
    return redirect('inbox')

@login_required
def reject_request(request, id):
    # Using ServiceBooking as the 'Request' model for this project
    req = get_object_or_404(ServiceBooking, id=id, receiver=request.user)
    req.status = 'rejected'
    req.save()
    messages.warning(request, 'Request rejected.')
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
    # Fetch all incoming messages and service requests (bookings)
    received_messages = Message.objects.filter(receiver=request.user)
    received_requests = ServiceBooking.objects.filter(receiver=request.user)
    
    # Combine and sort for a unified inbox experience
    # Note: ServiceBooking uses 'created_at', Message uses 'timestamp'
    items = list(received_messages) + list(received_requests)
    items.sort(key=lambda x: getattr(x, 'timestamp', getattr(x, 'created_at', None)), reverse=True)
    
    recent_services = ServicePost.objects.all()[:4]
    
    context = {
        'items': items,
        'received_requests': received_requests,
        'requests': received_requests, # Explicitly passed as requested
        'recent_services': recent_services
    }
    
    return render(request, 'inbox.html', context)

@login_required
def sent_messages(request):
    # Fetch all outgoing messages and service requests (bookings)
    sent_messages = Message.objects.filter(sender=request.user)
    sent_requests = ServiceBooking.objects.filter(sender=request.user)
    
    # Combine and sort for a unified sent view
    items = list(sent_messages) + list(sent_requests)
    items.sort(key=lambda x: getattr(x, 'timestamp', getattr(x, 'created_at', None)), reverse=True)
    
    recent_services = ServicePost.objects.all()[:4]
    
    context = {
        'items': items,
        'sent_requests': sent_requests,
        'requests': sent_requests, # Explicitly passed as requested
        'recent_services': recent_services
    }
    
    return render(request, 'sent_messages.html', context)

def search(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    
    results_services = ServicePost.objects.all()
    results_requests = ServiceRequest.objects.all()
    
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
        
    context = {
        'query': query,
        'location': location,
        'results_services': results_services,
        'results_requests': results_requests,
        'categories': CATEGORY_CHOICES,
        'selected_category': category
    }
    return render(request, 'search_results.html', context)

@login_required
def dashboard(request):
    user_services = ServicePost.objects.filter(author=request.user)
    user_requests = ServiceRequest.objects.filter(requester=request.user)
    
    # Recent bookings for dashboard
    incoming_bookings = ServiceBooking.objects.filter(receiver=request.user)[:5]
    sent_bookings = ServiceBooking.objects.filter(sender=request.user)[:5]
    
    received_messages = Message.objects.filter(receiver=request.user)[:5]
    sent_messages = Message.objects.filter(sender=request.user)[:5]
    
    return render(request, 'dashboard.html', {
        'user_services': user_services,
        'user_requests': user_requests,
        'incoming_bookings': incoming_bookings,
        'sent_bookings': sent_bookings,
        'received_messages': received_messages,
        'sent_messages': sent_messages,
    })

@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServicePost, pk=pk, author=request.user)
    service.delete()
    messages.success(request, 'Post deleted.')
    return redirect('dashboard')
@login_required
def payment_view(request, service_id):
    service = get_object_or_404(ServicePost, pk=service_id)
    
    # Negotiable services might have price as None, use a default placeholder or handle
    amount = service.price if service.price else 0
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # Save payment record
        payment = Payment.objects.create(
            user=request.user,
            service=service,
            amount=amount,
            payment_method=payment_method,
            status='success' # Simulation
        )
        
        # 1. Automatically create an accepted ServiceBooking
        if service.author:
            # DEBUG LOGGING
            print(f"--- DEBUG: AUTO PAYMENT BOOKING ---")
            print(f"Sender: {request.user.username}")
            print(f"Receiver (Owner): {service.author.username}")
            print(f"Service: {service.title}")
            print(f"-----------------------------------")

            booking = ServiceBooking.objects.create(
                sender=request.user,
                receiver=service.author,
                service=service,
                message=f"AUTOGENERATED: Payment of ₹{amount} confirmed via {payment_method.upper()}.",
                status='accepted'
            )
            
            # 2. Automatically create a confirmation Message for the Inbox
            Message.objects.create(
                sender=request.user,
                receiver=service.author,
                service=service,
                message=f"Hello! I've just completed the payment for your service '{service.title}'. Transaction ID: #SKL{payment.pk+10000}. Please check your bookings!"
            )
            messages.success(request, f'Payment of ₹{amount} was successful! Booking and confirmation sent.')
        else:
            messages.warning(request, f'Payment of ₹{amount} successful, but could not notify provider (Provider not found).')
        return redirect('payment_success', payment_id=payment.pk)
        
    return render(request, 'payment.html', {
        'service': service,
        'amount': amount
    })

@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)
    return render(request, 'payment_success.html', {'payment': payment})
