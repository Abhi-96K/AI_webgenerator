from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('generate/', views.generate_page, name='generate'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API endpoints  
    path('generator/generate/', views.generate_api, name='generate_api'),
    path('download/<int:site_id>/', views.download_site, name='download_site'),
    path('delete/<int:site_id>/', views.delete_site, name='delete_site'),
    
    # New pages
    path('help/', views.help_center, name='help_center'),
    path('contact/', views.contact_us, name='contact_us'),
    path('suggestions/', views.suggestion_box, name='suggestion'),
    path('pricing/', views.pricing, name='pricing'),
    path('subscription-plans/', views.pricing, name='subscription_plans'),
    path('payment/<str:plan>/', views.payment_page, name='payment_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('terms/', views.terms_conditions, name='terms_conditions'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('about/', views.about_us, name='about_us'),
    path('faq/', views.faq, name='faq'),
    path('generation-result/<int:site_id>/', views.generation_result, name='generation_result'),
    path('subscription/', views.subscription_management, name='subscription_management'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
]
