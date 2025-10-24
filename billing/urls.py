from django.urls import path
from . import views


urlpatterns = [
    path('plans/', views.plan_selection, name='plan_selection'),
    path('payment/<int:plan_id>/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('history/', views.payment_history, name='payment_history'),
]