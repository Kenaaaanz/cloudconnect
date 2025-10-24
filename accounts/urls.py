from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    
    # Security URLs
    path('change-password/', views.change_password, name='change_password'),
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('sessions/revoke/<int:session_id>/', views.revoke_session, name='revoke_session'),
    
    # Preferences & Settings URLs
    path('update-notifications/', views.update_notifications, name='update_notifications'),
    path('update-preferences/', views.update_preferences, name='update_preferences'),
    path('update-billing-address/', views.update_billing_address, name='update_billing_address'),
    
    # Data Management URLs
    path('export-data/', views.export_data, name='export_data'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # Paystack URLs - Specific patterns first
    path('paystack/subscribe/<int:plan_id>/', views.paystack_subscribe_with_plan, name='paystack_subscribe_plan'),
    path('paystack/initiate-payment/<int:plan_id>/', views.initiate_paystack_payment, name='initiate_paystack_payment'),
    path('paystack/verify/<str:reference>/', views.paystack_verify_payment, name='paystack_verify_payment'),
    
    # General patterns last
    path('paystack/subscribe/', views.paystack_subscribe, name='paystack_subscribe'),
]