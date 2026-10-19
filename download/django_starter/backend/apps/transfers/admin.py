"""
Transfers Admin
"""
from django.contrib import admin
from .models import TransferHeader, TransferLine, TransferSuggestion


class TransferLineInline(admin.TabularInline):
    model = TransferLine
    extra = 1
    fields = ('product', 'lot', 'qty', 'expiry_date')
    readonly_fields = ('expiry_date',)


@admin.register(TransferHeader)
class TransferHeaderAdmin(admin.ModelAdmin):
    list_display = ('transfer_no', 'from_store', 'to_store', 'transfer_date',
                    'status', 'initiator', 'receiver')
    list_filter = ('status', 'transfer_date', 'from_store', 'to_store')
    search_fields = ('transfer_no', 'reason')
    date_hierarchy = 'transfer_date'
    inlines = [TransferLineInline]


@admin.register(TransferLine)
class TransferLineAdmin(admin.ModelAdmin):
    list_display = ('transfer', 'product', 'lot', 'qty', 'expiry_date')
    list_filter = ('expiry_date',)


@admin.register(TransferSuggestion)
class TransferSuggestionAdmin(admin.ModelAdmin):
    list_display = ('lot', 'from_store', 'to_store', 'qty', 'urgency',
                    'score', 'is_approved', 'is_processed', 'created_at')
    list_filter = ('urgency', 'is_approved', 'is_processed', 'created_at')
    search_fields = ('lot__batch_no',)
    ordering = ('-score', '-created_at')
    readonly_fields = ('score', 'processed_at')
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        from .services import TransferSuggesterService
        count = 0
        for s in queryset.filter(is_processed=False):
            try:
                TransferSuggesterService.approve_suggestion(
                    suggestion_id=s.id, approved_by=request.user,
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} پیشنهاد تأیید شد')
    approve_selected.short_description = 'تأیید پیشنهادهای انتخاب‌شده'
