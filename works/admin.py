from django.contrib import admin
from .models import Work, Purchase, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'moderation_status', 'created_at')
    list_filter = ('moderation_status', 'created_at', 'categories')
    search_fields = ('title', 'author__username')
    list_editable = ('moderation_status',)
    filter_horizontal = ('categories',)  # Для удобного выбора категорий

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'amount', 'purchase_date')
    list_filter = ('purchase_date',)