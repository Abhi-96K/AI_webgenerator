from django.contrib import admin
from .models import GeneratedSite, UserProfile, Suggestion, Payment


@admin.register(GeneratedSite)
class GeneratedSiteAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at', 'generation_time']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'prompt']
    readonly_fields = ['created_at', 'generation_time']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_plan', 'websites_generated', 'free_websites_remaining']
    list_filter = ['subscription_plan', 'email_verified']
    search_fields = ['user__username', 'user__email']


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'name', 'suggestion_type', 'priority', 'status', 'created_at']
    list_filter = ['suggestion_type', 'priority', 'status', 'created_at']
    search_fields = ['title', 'name', 'email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Suggestion Details', {
            'fields': ('title', 'name', 'email', 'suggestion_type', 'priority', 'description')
        }),
        ('Status & Notes', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at']
    list_filter = ['payment_method', 'status', 'subscription_plan', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at', 'qr_code_data']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('user', 'amount', 'currency', 'payment_method', 'transaction_id')
        }),
        ('Subscription Info', {
            'fields': ('subscription_plan', 'subscription_months')
        }),
        ('Status & References', {
            'fields': ('status', 'payment_reference')
        }),
        ('Technical Data', {
            'fields': ('qr_code_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
