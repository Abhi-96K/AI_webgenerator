from django.views.decorators.csrf import csrf_exempt
import os, zipfile, time, uuid, qrcode, io, base64
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from .models import GeneratedSite, UserProfile, Suggestion, Payment
from .ai_service import generate_website_code, save_website_as_zip
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse



def home(request):
    """Home page view"""
    return render(request, 'generator/home.html')


def generate_page(request):
    """Website generation page"""
    # Get prompt from URL parameter if available
    prompt = request.GET.get('prompt', '')
    
    context = {
        'initial_prompt': prompt,
    }
    
    # If user is authenticated, add usage info
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        context.update({
            'profile': profile,
            'remaining_websites': profile.get_remaining_websites(),
            'can_generate': profile.can_generate_website(),
        })
    
    return render(request, 'generator/generate.html', context)


@csrf_exempt
def generate_api(request):
    """API endpoint for website generation"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    
    prompt = request.POST.get("prompt")
    if not prompt:
        return JsonResponse({"error": "No prompt provided"}, status=400)
    
    if len(prompt.strip()) < 10:
        return JsonResponse({"error": "Prompt too short. Please provide more details."}, status=400)
    
    # Check user limits
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if not profile.can_generate_website():
            return JsonResponse({
                "error": "You've reached your free website generation limit. Please upgrade to continue creating amazing websites!",
                "upgrade_required": True,
                "redirect_url": "/pricing/",
                "subscription_plans_url": "/pricing/"
            }, status=403)
    else:
        # For anonymous users, we can still generate but won't save to their account
        pass
    
    try:
        start_time = time.time()
        
        # Create pending record
        site = GeneratedSite.objects.create(
            user=request.user if request.user.is_authenticated else None,
            prompt=prompt,
            status="pending"
        )
        
        # Call OpenAI
        code = generate_website_code(prompt)
        
        generation_time = time.time() - start_time
        
        if code.startswith("Error:"):
            site.status = "failed"
            site.save()
            return JsonResponse({"error": code}, status=500)
        
        # Save as professional .zip file with proper structure
        site.generation_time = generation_time
        save_website_as_zip(site, code)
        
        # Decrement user usage if authenticated
        if request.user.is_authenticated:
            profile.decrement_usage()
        
        # Return JSON for API calls or redirect for web interface
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "site_id": site.id,
                "download_url": site.generated_file.url,
                "generation_time": round(generation_time, 2),
                "message": "Website generated successfully!",
                "redirect_url": f"/generation-result/{site.id}/"
            })
        else:
            # Redirect to enhanced result page
            return redirect('generator:generation_result', site_id=site.id)
        
    except Exception as e:
        # Update site status to failed
        if 'site' in locals():
            site.status = "failed"
            site.save()
        
        return JsonResponse({"error": f"Generation failed: {str(e)}"}, status=500)


@login_required
def dashboard(request):
    """User dashboard view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's generated sites
    sites_list = GeneratedSite.objects.filter(user=request.user)
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        sites_list = sites_list.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        sites_list = sites_list.filter(
            Q(prompt__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(sites_list, 12)  # 12 sites per page
    page_number = request.GET.get('page')
    sites = paginator.get_page(page_number)
    
    # Calculate statistics
    total_sites = sites_list.count()
    completed_sites = sites_list.filter(status='completed').count()
    total_downloads = sites_list.aggregate(
        downloads=Sum('downloads_count')
    )['downloads'] or 0
    
    days_since_joined = (timezone.now() - request.user.date_joined).days
    
    context = {
        'profile': profile,
        'sites': sites,
        'total_sites': total_sites,
        'completed_sites': completed_sites,
        'total_downloads': total_downloads,
        'days_since_joined': days_since_joined,
        'remaining_websites': profile.get_remaining_websites(),
        'can_generate': profile.can_generate_website(),
    }
    
    return render(request, 'generator/dashboard.html', context)



def download_site(request, site_id):
    """Handle website download and track statistics"""
    try:
        site = get_object_or_404(GeneratedSite, id=site_id)
        
        # Check if user has permission to download
        if site.user and site.user != request.user and not request.user.is_staff:
            raise Http404("Site not found")
        
        # Increment download count
        site.downloads_count += 1
        site.save()
        
        if site.generated_file:
            response = HttpResponse(
                site.generated_file.read(),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="website_{site.id}.zip"'
            return response
        else:
            raise Http404("File not found")
            
    except Exception as e:
        raise Http404("Site not found")


@login_required
def delete_site(request, site_id):
    """Delete a generated website"""
    if request.method == 'POST':
        site = get_object_or_404(GeneratedSite, id=site_id, user=request.user)
        
        # Delete the file if it exists
        if site.generated_file:
            try:
                site.generated_file.delete()
            except:
                pass
        
        # Delete the database record
        site.delete()
        
        messages.success(request, 'Website deleted successfully.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('generator:dashboard')
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# ============== NEW PAGES ==============

def help_center(request):
    """Help Center page with contact information"""
    context = {
        'page_title': 'Help Center',
        'contact_email': '1.maulitraders@gmail.com',
        'contact_phones': ['9021100337', '90220330088'],
        'business_hours': '9:00 AM - 9:00 PM (Mon-Sat)',
        'response_time': '24 hours',
    }
    return render(request, 'pages/help_center.html', context)


def contact_us(request):
    """Contact Us page"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # You can send email or save to database here
        messages.success(request, 'Thank you for contacting us! We will get back to you within 24 hours.')
        return redirect('generator:contact_us')
    
    context = {
        'page_title': 'Contact Us',
        'contact_email': '1.maulitraders@gmail.com',
        'contact_phones': ['9021100337', '90220330088'],
        'address': 'Mumbai, Maharashtra, India',  # Update with your address
    }
    return render(request, 'pages/contact_us.html', context)


def suggestion_box(request):
    """Suggestion box for user feedback"""
    if request.method == 'POST':
        suggestion = Suggestion.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            suggestion_type=request.POST.get('suggestion_type'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            priority=request.POST.get('priority', 'medium')
        )
        messages.success(request, 'Thank you for your suggestion! We will review it carefully.')
        return redirect('generator:suggestion_box')
    
    # Get recent implemented suggestions to show
    implemented_suggestions = Suggestion.objects.filter(status='implemented')[:5]
    
    context = {
        'page_title': 'Suggestion Box',
        'implemented_suggestions': implemented_suggestions,
    }
    return render(request, 'pages/suggestion_box.html', context)


def generate_qr_code(data):
    """Generate QR code for payment"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Convert to base64 for embedding in HTML
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_code_base64


def pricing(request):
    """Pricing page with payment options - both authenticated and anonymous users can view"""
    plans = {
        'basic': {
            'price': 999, 
            'websites': 10, 
            'duration': '1 month', 
            'popular': False,
            'features': [
                '10 AI websites/month',
                'Advanced AI models',
                'Premium templates',
                'Email support',
                'Source code download',
                'Basic customization'
            ]
        },
        'premium': {
            'price': 1999, 
            'websites': 50, 
            'duration': '1 month', 
            'popular': True,
            'features': [
                '50 AI websites/month',
                'All AI models',
                'Premium templates & themes',
                'Priority support',
                'Advanced customization',
                'SEO optimization',
                'Custom domains ready',
                'Mobile responsive designs'
            ]
        },
        'enterprise': {
            'price': 4999, 
            'websites': 'Unlimited', 
            'duration': '1 month', 
            'popular': False,
            'features': [
                'Unlimited websites',
                'All premium features',
                '24/7 dedicated support',
                'White-label option',
                'API access',
                'Custom integrations',
                'Bulk generation',
                'Priority queue'
            ]
        },
    }
    
    context = {
        'page_title': 'Pricing Plans',
        'plans': plans,
    }
    
    # Add user context if authenticated
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        context.update({
            'user_profile': profile,
            'current_plan': profile.subscription_plan,
            'websites_remaining': profile.get_remaining_websites(),
            'subscription_active': profile.subscription_plan != 'free' and profile.subscription_expires and profile.subscription_expires > timezone.now()
        })
    
    return render(request, 'pages/pricing.html', context)


@login_required
def payment_page(request, plan):
    """Payment page with enhanced payment options and QR code generation"""
    plans = {
        'basic': {'price': Decimal('999.00'), 'name': 'Basic Plan', 'websites': 10, 'duration_days': 30},
        'premium': {'price': Decimal('1999.00'), 'name': 'Premium Plan', 'websites': 50, 'duration_days': 30},
        'enterprise': {'price': Decimal('4999.00'), 'name': 'Enterprise Plan', 'websites': 999, 'duration_days': 30},
    }
    
    if plan not in plans:
        messages.error(request, 'Invalid plan selected.')
        return redirect('generator:pricing')
    
    selected_plan = plans[plan]
    transaction_id = str(uuid.uuid4())[:12].upper()
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        amount=selected_plan['price'],
        payment_method='upi',
        transaction_id=transaction_id,
        subscription_plan=plan,
        subscription_months=1
    )
    
    # Generate UPI payment string
    upi_id = "runner.abhi01-1@okaxis"  # Replace with your UPI ID
    upi_payment_string = f"upi://pay?pa={upi_id}&pn=AI Website Generator&am={selected_plan['price']}&cu=INR&tn=Payment for {selected_plan['name']} - {transaction_id}"
    
    # Generate QR code
    qr_code_base64 = generate_qr_code(upi_payment_string)
    
    # Save QR code data to payment
    payment.qr_code_data = upi_payment_string
    payment.save()
    
    context = {
        'page_title': f'Payment - {selected_plan["name"]}',
        'plan': selected_plan,
        'plan_key': plan,
        'transaction_id': transaction_id,
        'qr_code': qr_code_base64,
        'upi_id': upi_id,
        'amount': selected_plan['price'],
        'payment': payment,
    }
    return render(request, 'pages/payment.html', context)


@login_required 
def payment_success(request):
    """Payment success page with enhanced handling"""
    transaction_id = request.GET.get('txn_id')
    payment = None
    
    context = {
        'transaction_id': transaction_id,
        'payment_successful': False,
        'subscription_activated': False,
    }
    
    if transaction_id:
        try:
            payment = Payment.objects.get(transaction_id=transaction_id, user=request.user)
            
            # Only process if payment is not already completed
            if payment.status != 'completed':
                payment.status = 'completed'
                payment.save()
                
                # Update user subscription
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.subscription_plan = payment.subscription_plan
                
                # Calculate expiration date based on plan
                duration_days = 30  # Default 30 days
                if payment.subscription_months > 1:
                    duration_days = payment.subscription_months * 30
                
                profile.subscription_expires = timezone.now() + timezone.timedelta(days=duration_days)
                
                # Reset website counts based on plan
                if payment.subscription_plan == 'basic':
                    profile.free_websites_remaining = 10
                elif payment.subscription_plan == 'premium':
                    profile.free_websites_remaining = 50
                elif payment.subscription_plan == 'enterprise':
                    profile.free_websites_remaining = 999
                
                profile.save()
                
                context.update({
                    'payment_successful': True,
                    'subscription_activated': True,
                    'plan_name': payment.subscription_plan.title(),
                    'amount_paid': payment.amount,
                    'websites_included': profile.free_websites_remaining,
                    'expiry_date': profile.subscription_expires,
                })
                
                messages.success(request, f'Welcome to {payment.subscription_plan.title()} Plan! Your subscription is now active.')
            else:
                # Payment already processed
                context.update({
                    'payment_successful': True,
                    'subscription_activated': True,
                    'plan_name': payment.subscription_plan.title(),
                    'amount_paid': payment.amount,
                    'already_processed': True,
                })
                
        except Payment.DoesNotExist:
            messages.error(request, 'Invalid transaction ID. Please contact support if you believe this is an error.')
            context['error'] = 'Invalid transaction ID'
    else:
        messages.warning(request, 'No transaction ID provided.')
        context['error'] = 'No transaction ID provided'
    
    context['payment'] = payment
    return render(request, 'pages/payment_success.html', context)


def terms_conditions(request):
    """Terms and Conditions page"""
    context = {
        'page_title': 'Terms and Conditions',
        'last_updated': '2024-09-14',
        'company_name': 'AI Website Generator',
    }
    return render(request, 'pages/terms_conditions.html', context)


def privacy_policy(request):
    """Privacy Policy page"""
    context = {
        'page_title': 'Privacy Policy',
        'last_updated': '2024-09-14',
        'company_name': 'AI Website Generator',
        'contact_email': 'privacy@aiwebgen.com',
    }
    return render(request, 'pages/privacy_policy.html', context)


def about_us(request):
    """About Us page"""
    context = {
        'page_title': 'About Us',
        'company_name': 'AI Website Generator',
        'founded_year': '2024',
        'team_size': '5+',
        'websites_generated': GeneratedSite.objects.filter(status='completed').count(),
    }
    return render(request, 'pages/about_us.html', context)


def faq(request):
    """Frequently Asked Questions page"""
    faqs = [
        {
            'question': 'How does the AI website generator work?',
            'answer': 'Our AI uses advanced language models to understand your requirements and generate complete HTML, CSS, and JavaScript code for your website.'
        },
        {
            'question': 'What types of websites can I generate?',
            'answer': 'You can generate various types of websites including business landing pages, portfolios, blogs, e-commerce sites, and more.'
        },
        {
            'question': 'How long does it take to generate a website?',
            'answer': 'Website generation typically takes 30-60 seconds depending on the complexity of your requirements.'
        },
        {
            'question': 'Can I customize the generated website?',
            'answer': 'Yes! You get the complete source code which you can modify, customize, and deploy anywhere you want.'
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept UPI payments, bank transfers, credit/debit cards, and digital wallets for Indian customers.'
        },
        {
            'question': 'Is there a refund policy?',
            'answer': 'Yes, we offer a 7-day money-back guarantee if you are not satisfied with our service.'
        },
    ]
    
    context = {
        'page_title': 'Frequently Asked Questions',
        'faqs': faqs,
    }
    return render(request, 'pages/faq.html', context)


@login_required
def subscription_management(request):
    """Subscription management page for users to view and manage their subscription"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get recent payments
    recent_payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Calculate usage statistics
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    websites_this_month = GeneratedSite.objects.filter(
        user=request.user,
        created_at__gte=current_month_start,
        status='completed'
    ).count()
    
    context = {
        'profile': profile,
        'recent_payments': recent_payments,
        'websites_this_month': websites_this_month,
        'websites_remaining': profile.get_remaining_websites(),
        'subscription_active': profile.subscription_plan != 'free' and profile.subscription_expires and profile.subscription_expires > timezone.now(),
        'days_remaining': (profile.subscription_expires - timezone.now()).days if profile.subscription_expires and profile.subscription_expires > timezone.now() else 0,
    }
    
    return render(request, 'pages/subscription_management.html', context)


@login_required
def cancel_subscription(request):
    """Cancel user subscription"""
    if request.method == 'POST':
        profile = request.user.userprofile
        profile.subscription_plan = 'free'
        profile.subscription_expires = None
        profile.free_websites_remaining = 0  # They've already used their free websites
        profile.save()
        
        messages.success(request, 'Your subscription has been cancelled. You can resubscribe anytime.')
        return redirect('generator:subscription_management')
    
    return redirect('generator:subscription_management')


def generation_result(request, site_id):
    """Enhanced website generation result page with animations"""
    try:
        site = get_object_or_404(GeneratedSite, id=site_id)
        
        # Check if user has permission to view this result
        if site.user and site.user != request.user and not request.user.is_staff:
            raise Http404("Site not found")
        
        context = {
            'site': site,
            'site_id': site.id,
            'generation_time': site.generation_time,
            'page_title': 'Website Generated Successfully',
        }
        
        return render(request, 'generator/generation_result.html', context)
        
    except GeneratedSite.DoesNotExist:
        raise Http404("Site not found")

