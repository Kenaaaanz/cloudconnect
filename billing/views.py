from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.conf import settings
from .models import Plan, Subscription, Payment
from .paystack import PaystackAPI
from datetime import datetime, timedelta
from .paystack import get_paystack_instance

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def plan_selection(request):
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'billing/plans.html', {'plans': plans})


@login_required
def initiate_payment(request, plan_id):
    plan = Plan.objects.get(id=plan_id)
    paystack = get_paystack_instance()
    
    # Generate a unique reference
    reference = f"WIFI_{get_random_string(10).upper()}"
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
        reference=reference,
        status='pending'
    )
    
    # Generate payment URL
    payment_url = paystack.generate_payment_link(
        request=request,
        email=request.user.email,
        amount=plan.price,
        reference=reference,
        plan_name=plan.name
    )
    
    if payment_url:
        return redirect(payment_url)
    else:
        messages.error(request, 'Failed to initialize payment. Please try again.')
        return redirect('plan_selection')

@login_required
def payment_callback(request):
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('dashboard')
    
    paystack = get_paystack_instance()
    
    # Verify transaction
    if paystack.is_transaction_successful(reference):
        # Get transaction details
        transaction_details = paystack.get_transaction_details(reference)
        
        # Update payment status
        payment = Payment.objects.get(reference=reference)
        payment.status = 'success'
        payment.paystack_reference = transaction_details.get('id', '')
        payment.save()
        
        # Update subscription (implementation depends on your model)
        # ...
        
        messages.success(request, 'Payment successful! Your subscription has been activated.')
        return redirect('dashboard')
    else:
        payment = Payment.objects.get(reference=reference)
        payment.status = 'failed'
        payment.save()
        
        messages.error(request, 'Payment failed. Please try again.')
        return redirect('plan_selection')
    
@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'billing/history.html', {'payments': payments})