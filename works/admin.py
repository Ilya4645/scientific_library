from django.contrib import admin
from .models import Work, Purchase

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'moderation_status', 'created_at')
    list_filter = ('moderation_status', 'created_at')
    search_fields = ('title', 'author__username')
    list_editable = ('moderation_status',)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'amount', 'purchase_date')
    list_filter = ('purchase_date',)