from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Ticket, TicketCategory, TicketMessage
from django.utils import timezone

class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1  # Allow adding new messages
    readonly_fields = ('created_at',)
    fields = ('sender', 'message', 'attachment', 'is_internal', 'created_at')
    
    def get_extra(self, request, obj=None, **kwargs):
        # Only show extra form if ticket exists (not when creating new ticket)
        if obj:
            return 1
        return 0
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sender":
            # Default sender to current admin user
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'user', 'category', 'priority', 'status_colored', 'assigned_to', 'last_message', 'created_at')
    list_filter = ('status', 'priority', 'category', 'assigned_to', 'created_at')
    search_fields = ('subject', 'user__username', 'user__email', 'description')
    list_editable = ('priority', 'assigned_to')  # Removed 'status' since we use 'status_colored'
    readonly_fields = ('user', 'created_at', 'updated_at', 'resolved_at', 'message_count', 'last_message_info')
    inlines = [TicketMessageInline]
    list_per_page = 25
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('user', 'category', 'subject', 'description')
        }),
        ('Management', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Statistics', {
            'fields': ('message_count', 'last_message_info'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'open': '#e74c3c',        # Red
            'in_progress': '#f39c12',  # Orange
            'waiting_for_user': '#3498db',  # Blue
            'resolved': '#2ecc71',     # Green
            'closed': '#95a5a6'        # Gray
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def last_message(self, obj):
        """Show last message date"""
        last_msg = obj.messages.last()
        if last_msg:
            return last_msg.created_at.strftime('%Y-%m-%d %H:%M')
        return '-'
    last_message.short_description = 'Last Message'
    
    def message_count(self, obj):
        """Show total message count"""
        total = obj.messages.count()
        public = obj.messages.filter(is_internal=False).count()
        internal = obj.messages.filter(is_internal=True).count()
        return f"Total: {total} (Public: {public}, Internal: {internal})"
    message_count.short_description = 'Messages'
    
    def last_message_info(self, obj):
        """Show detailed last message info"""
        last_msg = obj.messages.last()
        if last_msg:
            msg_type = "Internal" if last_msg.is_internal else "Public"
            return format_html(
                '<strong>{}:</strong> {} by {} on {}',
                msg_type,
                last_msg.message[:100] + ('...' if len(last_msg.message) > 100 else ''),
                last_msg.sender.get_full_name(),
                last_msg.created_at.strftime('%Y-%m-%d %H:%M')
            )
        return 'No messages'
    last_message_info.short_description = 'Last Message Details'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'user', 'category', 'assigned_to'
        ).prefetch_related('messages')
    
    def save_model(self, request, obj, form, change):
        """Auto-assign to current admin if not assigned"""
        if not obj.assigned_to and request.user.is_staff:
            obj.assigned_to = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """Handle message formset saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketMessage):
                if not instance.sender:
                    instance.sender = request.user
                instance.save()
        formset.save_m2m()

    def mark_as_in_progress(self, request, queryset):
        """Mark selected tickets as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} tickets marked as in progress.')
    mark_as_in_progress.short_description = "Mark selected tickets as in progress"

    def mark_as_resolved(self, request, queryset):
        """Mark selected tickets as resolved"""
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} tickets marked as resolved.')
    mark_as_resolved.short_description = "Mark selected tickets as resolved"

    def assign_to_me(self, request, queryset):
        """Assign selected tickets to current admin"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} tickets assigned to you.')
    assign_to_me.short_description = "Assign selected tickets to me"

    actions = [mark_as_in_progress, mark_as_resolved, assign_to_me]

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket_link', 'sender', 'message_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at', 'sender')
    search_fields = ('ticket__subject', 'sender__username', 'message')
    readonly_fields = ('created_at',)
    raw_id_fields = ('ticket',)
    
    def ticket_link(self, obj):
        """Create clickable link to ticket"""
        url = reverse('admin:support_ticket_change', args=[obj.ticket.id])
        return format_html('<a href="{}">{}</a>', url, obj.ticket.subject)
    ticket_link.short_description = 'Ticket'
    
    def message_preview(self, obj):
        """Show message preview"""
        return obj.message[:100] + ('...' if len(obj.message) > 100 else '')
    message_preview.short_description = 'Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'sender')