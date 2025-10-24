"""
URL configuration for cloudconnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# wifi_billing/urls.py
from django.contrib import admin  # Add this import at the top
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from accounts.admin_views import superadmin_dashboard, analytics_detail  # Import the views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard
from accounts import views  

#from accounts.views import auth_test, test_login


urlpatterns = [
    path('admin/', admin.site.urls),  # This should already exist
    
    # Add the superadmin dashboard URL pattern
    path('admin/dashboard/', admin.site.admin_view(superadmin_dashboard), name='superadmin_dashboard'),
    path('admin/analytics/<str:chart_type>/', admin.site.admin_view(analytics_detail), name='analytics_detail'),
    path('accounts/', include('accounts.urls')),

    # Your existing URLs
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', account_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('billing/', include('billing.urls')),
    path('router/', include('router_manager.urls')),
    path('profile/', account_views.profile, name='profile'),
    
    #path('test/login/', test_login, name='test_login'),
    #('test/auth/', auth_test, name='auth_test'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Paystack URLs in main urls.py
    path('paystack/subscribe/<int:plan_id>/', views.paystack_subscribe_with_plan, name='paystack_subscribe_plan'),
    path('paystack/verify/<str:reference>/', views.paystack_verify_payment, name='paystack_verify_payment'),
    path('paystack/subscribe/', views.paystack_subscribe, name='paystack_subscribe'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)