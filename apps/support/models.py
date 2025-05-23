from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class TicketCategory(models.Model):
    """Ticket Categories"""
    name = models.CharField(max_length=100, verbose_name="Category Name")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket Category"
        verbose_name_plural = "Ticket Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Ticket(models.Model):
    """Support Ticket"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_for_user', 'Waiting for User'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', verbose_name="User")
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True, verbose_name="Category")
    subject = models.CharField(max_length=200, verbose_name="Subject")
    description = models.TextField(verbose_name="Description")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Status")
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets',
        limit_choices_to={'is_staff': True},
        verbose_name="Assigned To"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resolved At")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.subject}"

    def save(self, *args, **kwargs):
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
        super().save(*args, **kwargs)

class TicketMessage(models.Model):
    """Ticket Messages"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', verbose_name="Ticket")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Sender")
    message = models.TextField(verbose_name="Message")
    attachment = models.FileField(upload_to='ticket_attachments/', null=True, blank=True, verbose_name="Attachment")
    is_internal = models.BooleanField(default=False, verbose_name="Internal Message", 
                                    help_text="Internal messages are only visible to staff")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Ticket Message"
        verbose_name_plural = "Ticket Messages"
        ordering = ['created_at']

    def __str__(self):
        msg_type = "Internal" if self.is_internal else "Public"
        return f"{msg_type} Message #{self.id} for Ticket #{self.ticket.id}"