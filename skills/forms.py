from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Service, HelpRequest, Message, Review, Request, LOCATION_CHOICES, SERVICE_TYPE_CHOICES

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'email')

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'email', 'phone', 'skills_offered', 'location', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell others about yourself...'}),
            'skills_offered': forms.TextInput(attrs={'placeholder': 'e.g. Python, Math Tutoring'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['email'].initial = self.instance.user.email
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile

class ServiceForm(forms.ModelForm):
    custom_category = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Specify your custom category (e.g. Logo Design, Yoga)'})
    )

    class Meta:
        model = Service
        fields = ['title', 'description', 'category', 'custom_category', 'image', 'payment_type', 'price', 'location', 'service_type', 'payment_method', 'delivery_time']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter a catchy title for your service'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe what you offer in detail...'}),
            'price': forms.NumberInput(attrs={'placeholder': '0.00'}),
            'location': forms.Select(
                choices=[('', '— Select City —')] + list(LOCATION_CHOICES),
                attrs={'class': 'form-select'}
            ),
            'service_type': forms.Select(
                choices=SERVICE_TYPE_CHOICES,
                attrs={'class': 'form-select', 'id': 'id_service_type'}
            ),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'delivery_time': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_type'].required = True
        self.fields['location'].required = True
        self.fields['service_type'].required = True
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['location'].widget.attrs.update({'class': 'form-select'})
        self.fields['service_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['category'].widget.attrs.update({'id': 'id_category'})
        self.fields['custom_category'].widget.attrs.update({'id': 'id_custom_category'})
        self.fields['payment_type'].widget.attrs.update({'id': 'id_payment_type'})
        self.fields['price'].widget.attrs.update({'id': 'id_price'})

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        custom = cleaned_data.get('custom_category')
        payment_type = cleaned_data.get('payment_type')
        price = cleaned_data.get('price')

        # Handle "Other" category replacement
        if category == 'other':
            if not custom:
                self.add_error('custom_category', 'Please specify your custom category.')
            else:
                cleaned_data['category'] = custom

        # Conditional validation for Price
        if payment_type == 'paid':
            if not price or price <= 0:
                self.add_error('price', 'Please specify a valid price for your paid service.')
        else:
            cleaned_data['price'] = None

        return cleaned_data

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional: Add a message for the provider...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs.update({'class': 'form-control'})

class HelpRequestForm(forms.ModelForm):
    custom_category = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Specify your custom skill need...'})
    )

    class Meta:
        model = HelpRequest
        fields = ['title', 'description', 'category', 'custom_category', 'budget']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'What are you looking for?'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide details about the help you need...'}),
            'budget': forms.TextInput(attrs={'placeholder': 'e.g., Free, ₹500, Negotiable'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'id': 'id_category_req'})
        self.fields['custom_category'].widget.attrs.update({'id': 'id_custom_category_req'})

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        custom = cleaned_data.get('custom_category')
        
        if category == 'other':
            if not custom:
                self.add_error('custom_category', 'Please specify your custom requirement.')
            else:
                cleaned_data['category'] = custom
        return cleaned_data

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].widget.attrs.update({'class': 'form-control'})
        self.fields['message'].label = ""

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your experience...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
