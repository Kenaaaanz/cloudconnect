from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django_countries import countries
import json
import csv
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
import requests
from .models import CustomUser, UserSession, LoginHistory
from .forms import (RegistrationForm, UserUpdateForm, PasswordChangeForm, 
                   NotificationPreferencesForm, AccountPreferencesForm, BillingAddressForm, UserProfileForm, CustomPasswordChangeForm)
from billing.models import Subscription, Payment, Plan
from router_manager.models import Router
from django.contrib.auth.forms import AuthenticationForm

# Paystack configuration
PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', 'your_paystack_secret_key_here')
PAYSTACK_PUBLIC_KEY = getattr(settings, 'PAYSTACK_PUBLIC_KEY', 'your_paystack_public_key_here')

def get_client_ip(request):
    """Utility function to get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            try:
                user = registration_form.save()
                login(request, user)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
                messages.success(request, 'Registration successful! Welcome to ConnectWise.')
                return redirect('dashboard')
            except Exception as e:
                print(f"Error during registration: {e}")
                messages.error(request, f'Registration error: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        registration_form = RegistrationForm()
    return render(request, 'accounts/register.html', {'registration_form': registration_form})

@login_required
def dashboard(request):
    try:
        subscription = Subscription.objects.get(user=request.user, is_active=True)
    except Subscription.DoesNotExist:
        subscription = None
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:5]
    try:
        router = Router.objects.get(user=request.user)
    except Router.DoesNotExist:
        router = None
    context = {
        'subscription': subscription,
        'payments': payments,
        'router': router
    }
    return render(request, 'accounts/dashboard.html', context)

try:
    from billing.models import Subscription, Payment, Plan
    BILLING_ENABLED = True
except ImportError:
    BILLING_ENABLED = False
    print("Billing app not available - billing features disabled")


@login_required
def profile(request):
    user = request.user
    
    # Initialize billing variables
    active_subscription = None
    payment_history = []
    available_plans = []
    
    # Get billing data only if billing app is available
    if BILLING_ENABLED:
        try:
            active_subscription = Subscription.objects.filter(
                user=user, 
                is_active=True,
                end_date__gte=timezone.now()
            ).select_related('plan').first()
        except Exception as e:
            print(f"Error getting subscription: {e}")
            active_subscription = None
        
        try:
            payment_history = Payment.objects.filter(user=user).select_related('plan').order_by('-created_at')[:10]
        except Exception as e:
            print(f"Error getting payment history: {e}")
            payment_history = []
        
        try:
            available_plans = Plan.objects.filter(is_active=True)
        except Exception as e:
            print(f"Error getting available plans: {e}")
            available_plans = []
    
    # Handle POST requests - REMOVE billing address handling from here
    if request.method == 'POST':
        # Handle account deletion
        if 'delete_account' in request.POST:
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        
        # Handle profile update (personal info only)
        elif 'update_profile' in request.POST:
            form = UserProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        
        # Handle password change
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully!')
                return redirect('profile')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)
        
        # Handle session revocation
        elif 'revoke_session' in request.POST:
            session_key = request.POST.get('session_key')
            if session_key:
                try:
                    session = UserSession.objects.get(session_key=session_key, user=request.user)
                    session.is_active = False
                    session.save()
                    messages.success(request, 'Session revoked successfully.')
                except UserSession.DoesNotExist:
                    messages.error(request, 'Session not found.')
            return redirect('profile')
        
         # Handle plan upgrade
        elif 'upgrade_plan' in request.POST:
            plan_id = request.POST.get('plan_id')
            if plan_id and BILLING_ENABLED:
                try:
                    plan = Plan.objects.get(id=plan_id, is_active=True)
                    # Redirect to Paystack payment
                    return redirect('paystack_subscribe_plan', plan_id=plan_id)
                except Plan.DoesNotExist:
                    messages.error(request, 'Selected plan not found.')
                except Exception as e:
                    messages.error(request, f'Error processing plan upgrade: {str(e)}')
            else:
                messages.error(request, 'Invalid plan selected.')
        

    
    # Initialize forms for GET requests or failed POST requests
    form = UserProfileForm(instance=user)
    password_form = CustomPasswordChangeForm(user)
    
    # Get active sessions
    active_sessions = UserSession.objects.filter(user=user, is_active=True).order_by('-last_activity')
    
    context = {
        'form': form,
        'password_form': password_form,
        'active_sessions': active_sessions,
        'active_subscription': active_subscription,
        'payment_history': payment_history,
        'available_plans': available_plans,
        'countries': list(countries),
        'billing_enabled': BILLING_ENABLED,
    }
    
    return render(request, 'accounts/profile.html', context)
# Helper function for confirmation
def confirm(message):
    """Simple confirmation helper"""
    return True

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def update_notifications(request):
    user = request.user
    if request.method == 'POST':
        user.email_notifications = 'email_notifications' in request.POST
        user.sms_notifications = 'sms_notifications' in request.POST
        user.billing_reminders = 'billing_reminders' in request.POST
        user.service_updates = 'service_updates' in request.POST
        user.promotional_offers = 'promotional_offers' in request.POST
        user.save()
        messages.success(request, 'Notification preferences updated!')
    return redirect('profile')


def update_billing_address(request):
    """
    Handle billing address updates
    """
    user = request.user
    
    try:
        # Get address fields from the request
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        country = request.POST.get('country', '').strip()
        
        # Update user address fields
        if address:
            user.address = address
        if city:
            user.city = city
        if state:
            user.state = state
        if zip_code:
            user.zip_code = zip_code
        if country:
            user.country = country
        
        # Save the user object
        user.save()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Billing address updated successfully!',
                'billing_address': user.billing_address
            })
        else:
            messages.success(request, 'Billing address updated successfully!')
            return redirect('profile')
            
    except Exception as e:
        error_message = f'Error updating billing address: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=400)
        else:
            messages.error(request, error_message)
            return redirect('profile')

@login_required
@require_POST
def update_preferences(request):
    """
    Handle user preference updates via AJAX or form submission
    """
    user = request.user
    
    try:
        # Update language preference
        if 'language' in request.POST:
            user.language = request.POST.get('language')
        
        # Update timezone preference
        if 'timezone' in request.POST:
            user.timezone = request.POST.get('timezone')
        
        # Update date format preference
        if 'date_format' in request.POST:
            user.date_format = request.POST.get('date_format')
        
        # Update dark mode preference
        user.dark_mode = 'dark_mode' in request.POST
        
        # Update notification preferences
        user.email_notifications = 'email_notifications' in request.POST
        user.sms_notifications = 'sms_notifications' in request.POST
        user.billing_reminders = 'billing_reminders' in request.POST
        user.service_updates = 'service_updates' in request.POST
        user.promotional_offers = 'promotional_offers' in request.POST
        
        # Save the user object
        user.save()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Preferences updated successfully!'
            })
        else:
            messages.success(request, 'Preferences updated successfully!')
            return redirect('profile')
            
    except Exception as e:
        error_message = f'Error updating preferences: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=400)
        else:
            messages.error(request, error_message)
            return redirect('profile')

@login_required
@require_http_methods(["POST"])
def revoke_session(request, session_id):
    """
    Revoke a specific user session
    """
    user = request.user
    
    try:
        # Get the session to revoke
        session = get_object_or_404(UserSession, id=session_id, user=user)
        
        # Don't allow revoking the current session
        if session.session_key == request.session.session_key:
            messages.error(request, 'Cannot revoke your current active session.')
            return redirect('profile')
        
        # Revoke the session
        session.is_active = False
        session.save()
        
        messages.success(request, 'Session revoked successfully.')
        
    except Exception as e:
        messages.error(request, f'Error revoking session: {str(e)}')
    
    return redirect('profile')

@login_required
@require_POST
def enable_2fa(request):
    """
    Enable two-factor authentication
    """
    user = request.user
    
    try:
        # In a real implementation, you would integrate with a 2FA library like django-otp
        # For now, we'll just update the flag
        user.two_factor_enabled = True
        user.save()
        
        messages.success(request, 'Two-factor authentication has been enabled successfully!')
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Two-factor authentication enabled successfully!',
                'two_factor_enabled': True
            })
            
    except Exception as e:
        error_message = f'Error enabling two-factor authentication: {str(e)}'
        messages.error(request, error_message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=400)
    
    return redirect('profile')

@login_required
@require_POST
def disable_2fa(request):
    """
    Disable two-factor authentication
    """
    user = request.user
    
    try:
        user.two_factor_enabled = False
        user.save()
        
        messages.success(request, 'Two-factor authentication has been disabled.')
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Two-factor authentication disabled successfully!',
                'two_factor_enabled': False
            })
            
    except Exception as e:
        error_message = f'Error disabling two-factor authentication: {str(e)}'
        messages.error(request, error_message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=400)
    
    return redirect('profile')

@login_required
def export_data(request):
    """
    Export user data in JSON or CSV format
    """
    user = request.user
    format_type = request.GET.get('format', 'json')
    
    try:
        # Prepare user data for export
        user_data = {
            'profile': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company_account_number': user.company_account_number,
                'phone': str(user.phone) if user.phone else None,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'country': str(user.country) if user.country else None,
                'zip_code': user.zip_code,
                'account_type': user.account_type,
                'date_joined': user.date_joined.isoformat(),
            },
            'preferences': {
                'language': user.language,
                'timezone': user.timezone,
                'date_format': user.date_format,
                'dark_mode': user.dark_mode,
                'email_notifications': user.email_notifications,
                'sms_notifications': user.sms_notifications,
                'billing_reminders': user.billing_reminders,
                'service_updates': user.service_updates,
                'promotional_offers': user.promotional_offers,
            },
            'security': {
                'two_factor_enabled': user.two_factor_enabled,
                'last_password_change': user.last_password_change.isoformat(),
            }
        }
        
        # Add sessions data
        sessions = UserSession.objects.filter(user=user)
        user_data['sessions'] = [
            {
                'device_type': session.device_type,
                'ip_address': str(session.ip_address),
                'location': session.location,
                'last_activity': session.last_activity.isoformat(),
                'is_active': session.is_active,
            }
            for session in sessions
        ]
        
        # Add billing data if available
        if BILLING_ENABLED:
            try:
                subscriptions = Subscription.objects.filter(user=user)
                payments = Payment.objects.filter(user=user)
                
                user_data['billing'] = {
                    'subscriptions': [
                        {
                            'plan': sub.plan.name,
                            'start_date': sub.start_date.isoformat(),
                            'end_date': sub.end_date.isoformat(),
                            'is_active': sub.is_active,
                            'auto_renew': sub.auto_renew,
                        }
                        for sub in subscriptions
                    ],
                    'payments': [
                        {
                            'plan': payment.plan.name,
                            'amount': float(payment.amount),
                            'reference': payment.reference,
                            'status': payment.status,
                            'created_at': payment.created_at.isoformat(),
                        }
                        for payment in payments
                    ]
                }
            except Exception as e:
                user_data['billing'] = {'error': str(e)}
        
        if format_type == 'csv':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{user.username}_data_export.csv"'
            
            writer = csv.writer(response)
            
            # Write profile data
            writer.writerow(['Section', 'Field', 'Value'])
            for section, data in user_data.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (list, dict)):
                            writer.writerow([section, key, json.dumps(value, default=str)])
                        else:
                            writer.writerow([section, key, str(value)])
            
            return response
        
        else:
            # Default to JSON
            response = JsonResponse(user_data, json_dumps_params={'indent': 2})
            response['Content-Disposition'] = f'attachment; filename="{user.username}_data_export.json"'
            return response
            
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('profile')
    
@login_required
def paystack_subscribe(request):
    """Handle general subscription (no specific plan)"""
    if not BILLING_ENABLED:
        messages.error(request, 'Billing is not enabled on this system.')
        return redirect('profile')
    
    # Redirect to profile where they can choose a plan
    messages.info(request, 'Please select a specific plan to subscribe.')
    return redirect('profile')

@login_required
def paystack_subscribe_with_plan(request, plan_id):
    """Handle subscription with specific plan - Complete working version"""
    if not BILLING_ENABLED:
        messages.error(request, 'Billing is not enabled on this system.')
        return redirect('profile')
    
    try:
        # Get the plan
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        
        # Generate unique reference
        import uuid
        reference = f"sub_{request.user.id}_{uuid.uuid4().hex[:8]}"
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            reference=reference,
            status='pending'
        )
        
        # Paystack configuration
        PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', 'your_secret_key_here')
        
        # Paystack payment data
        paystack_data = {
            'email': request.user.email,
            'amount': int(plan.price * 100),  # Convert to kobo
            'reference': reference,
            'callback_url': request.build_absolute_uri(f'/accounts/paystack/verify/{reference}/'),
            'metadata': {
                'user_id': request.user.id,
                'plan_id': plan.id,
                'payment_id': payment.id,
                'custom_fields': [
                    {
                        'display_name': "Plan Name",
                        'variable_name': "plan_name", 
                        'value': plan.name
                    },
                    {
                        'display_name': "Customer Name", 
                        'variable_name': "customer_name",
                        'value': f"{request.user.first_name} {request.user.last_name}"
                    }
                ]
            }
        }
        
        # Initialize Paystack transaction
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        import requests
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            json=paystack_data,
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status']:
                # Success - redirect to Paystack payment page
                authorization_url = data['data']['authorization_url']
                messages.success(request, f'Redirecting to Paystack for {plan.name} subscription...')
                return redirect(authorization_url)
            else:
                # Paystack API returned error
                error_message = data.get('message', 'Unknown Paystack error')
                payment.status = 'failed'
                payment.save()
                messages.error(request, f'Paystack error: {error_message}')
        else:
            # HTTP error
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Unable to connect to Paystack. Please try again.')
            
    except Plan.DoesNotExist:
        messages.error(request, 'Selected plan not found or is no longer available.')
    except requests.exceptions.RequestException as e:
        # Network-related errors
        messages.error(request, 'Network error. Please check your connection and try again.')
        print(f"Paystack network error: {e}")
    except Exception as e:
        # Any other unexpected errors
        messages.error(request, 'An unexpected error occurred. Please try again.')
        print(f"Paystack subscription error: {e}")
    
    return redirect('profile')

@login_required
def paystack_verify_payment(request, reference):
    """Verify Paystack payment and activate subscription"""
    if not BILLING_ENABLED:
        messages.error(request, 'Billing is not enabled on this system.')
        return redirect('profile')
    
    try:
        # Get the payment record
        payment = get_object_or_404(Payment, reference=reference, user=request.user)
        
        # Skip if already processed
        if payment.status == 'success':
            messages.info(request, 'Payment already processed successfully.')
            return redirect('dashboard')
        
        # Verify payment with Paystack
        PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', 'your_secret_key_here')
        
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        import requests
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                # Payment successful
                payment_data = data['data']
                
                # Update payment record
                payment.status = 'success'
                payment.paystack_reference = payment_data['id']
                payment.transaction_date = payment_data['paid_at']
                payment.save()
                
                # Get the plan
                plan = payment.plan
                
                # Deactivate any existing subscriptions
                Subscription.objects.filter(user=request.user, is_active=True).update(is_active=False)
                
                # Create new subscription
                from django.utils import timezone
                from datetime import timedelta
                
                subscription = Subscription.objects.create(
                    user=request.user,
                    plan=plan,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),  # 30-day subscription
                    is_active=True,
                    auto_renew=True
                )
                
                messages.success(request, f'Successfully subscribed to {plan.name}! Your subscription is now active.')
                return redirect('dashboard')
            
            else:
                # Payment failed or pending
                payment.status = 'failed'
                payment.save()
                
                error_message = data['data'].get('gateway_response', 'Payment failed')
                messages.error(request, f'Payment failed: {error_message}')
                
        else:
            # HTTP error during verification
            messages.error(request, 'Error verifying payment with Paystack. Please contact support.')
            
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
    except requests.exceptions.RequestException as e:
        messages.error(request, 'Network error during payment verification. Please check your subscription status.')
        print(f"Paystack verification network error: {e}")
    except Exception as e:
        messages.error(request, 'An unexpected error occurred during payment verification.')
        print(f"Paystack verification error: {e}")
    
    return redirect('profile')

@login_required
def initiate_paystack_payment(request, plan_id):
    """
    AJAX endpoint to initiate Paystack payment (for JavaScript integration)
    """
    if not BILLING_ENABLED:
        return JsonResponse({
            'status': 'error',
            'message': 'Billing is not enabled on this system.'
        })
    
    if request.method == 'POST':
        try:
            plan = get_object_or_404(Plan, id=plan_id, is_active=True)
            
            # Generate unique reference
            import uuid
            reference = f"sub_{request.user.id}_{uuid.uuid4().hex[:8]}"
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                reference=reference,
                status='pending'
            )
            
            # Paystack payment data
            paystack_data = {
                'email': request.user.email,
                'amount': int(plan.price * 100),  # Convert to kobo
                'reference': reference,
                'callback_url': request.build_absolute_uri(f'/paystack/verify/{reference}/'),
                'metadata': {
                    'user_id': request.user.id,
                    'plan_id': plan.id,
                    'payment_id': payment.id,
                }
            }
            
            # Initialize Paystack transaction
            headers = {
                'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                json=paystack_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    return JsonResponse({
                        'status': 'success',
                        'payment_url': data['data']['authorization_url'],
                        'reference': reference
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to initialize payment with Paystack.'
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error connecting to Paystack.'
                })
                
        except Plan.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Selected plan not found.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing payment: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })

@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """
    Handle account deletion with confirmation
    """
    user = request.user
    
    if request.method == 'POST':
        try:
            # Double-check confirmation
            confirmation = request.POST.get('confirmation', '')
            if confirmation != 'DELETE MY ACCOUNT':
                messages.error(request, 'Please type "DELETE MY ACCOUNT" to confirm deletion.')
                return redirect('profile')
            
            # Log out the user before deleting account
            from django.contrib.auth import logout
            logout(request)
            
            # Delete the user account
            user.delete()
            
            messages.success(request, 'Your account has been permanently deleted. We hope to see you again!')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
            return redirect('profile')
    
    # GET request - show confirmation page
    return render(request, 'accounts/delete_account_confirm.html', {
        'user': user
    })