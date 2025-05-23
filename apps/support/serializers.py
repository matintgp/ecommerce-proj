from rest_framework import serializers
from django.utils import timezone
from .models import Ticket, TicketCategory, TicketMessage

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description']

class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = ['id', 'message', 'attachment', 'sender_name', 'sender_email', 'created_at']
        read_only_fields = ['id', 'sender_name', 'sender_email', 'created_at']

class TicketCreateSerializer(serializers.ModelSerializer):
    initial_message = serializers.CharField(write_only=True, help_text="Initial message for the ticket")
    
    class Meta:
        model = Ticket
        fields = ['category', 'subject', 'description', 'priority', 'initial_message']
    
    def create(self, validated_data):
        initial_message = validated_data.pop('initial_message', None)
        ticket = super().create(validated_data)
        
        # Create initial message if provided
        if initial_message:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=ticket.user,
                message=initial_message,
                is_internal=False
            )
        
        return ticket

class TicketSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    can_user_reply = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'subject', 'description', 'priority', 'status',
            'user_name', 'user_email', 'category_name', 'assigned_to_name',
            'created_at', 'updated_at', 'resolved_at',
            'messages', 'messages_count', 'last_message_at', 'can_user_reply'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resolved_at']
    
    def get_messages_count(self, obj):
        return obj.messages.filter(is_internal=False).count()
    
    def get_last_message_at(self, obj):
        last_msg = obj.messages.filter(is_internal=False).last()
        return last_msg.created_at if last_msg else None
    
    def get_can_user_reply(self, obj):
        """Check if user can reply to this ticket"""
        request = self.context.get('request')
        if not request:
            return False
        
        # Staff can always reply
        if request.user.is_staff:
            return True
        
        # Regular users cannot reply to resolved/closed tickets
        if obj.status in ['resolved', 'closed']:
            return False
        
        return True

class TicketManageSerializer(serializers.Serializer):
    """Serializer for the manage_ticket endpoint"""
    message = serializers.CharField(required=False, help_text="Add a message to the ticket")
    attachment = serializers.FileField(required=False, help_text="Optional file attachment")
    status = serializers.ChoiceField(choices=Ticket.STATUS_CHOICES, required=False, help_text="Change ticket status (staff only)")
    priority = serializers.ChoiceField(choices=Ticket.PRIORITY_CHOICES, required=False, help_text="Change ticket priority")
    assigned_to = serializers.IntegerField(required=False, help_text="Assign to staff member ID (0 to unassign, staff only)")