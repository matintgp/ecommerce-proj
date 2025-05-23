from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Ticket, TicketCategory, TicketMessage
from .serializers import *

class IsOwnerOrStaff(permissions.BasePermission):
    """Users can only see their own tickets, unless they are staff"""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff

class TicketCategoryViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """List of ticket categories"""
    queryset = TicketCategory.objects.filter(is_active=True)
    serializer_class = TicketCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=["Support"],
        operation_summary="List ticket categories (just for getting available categories if u want [ not used in the app])",
        operation_description="Get list of available ticket categories\n(just for getting available categories if u want [ not used in the app])"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)





class TicketViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Support ticket management - Simplified with combined actions"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ticket.objects.none()
        
        user = self.request.user
        if user.is_staff:
            return Ticket.objects.all().select_related('user', 'category', 'assigned_to').prefetch_related('messages')
        return Ticket.objects.filter(user=user).select_related('user', 'category', 'assigned_to').prefetch_related('messages')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        elif self.action == 'manage_ticket':
            return TicketManageSerializer
        return TicketSerializer
    
    @swagger_auto_schema(
        tags=["Support"],
        operation_summary="List tickets",
        operation_description="Get list of user's tickets (or all tickets for staff) along with available categories",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('priority', openapi.IN_QUERY, description="Filter by priority", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Get categories
        categories = TicketCategory.objects.filter(is_active=True)
        categories_data = TicketCategorySerializer(categories, many=True).data
        
        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            tickets_serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(tickets_serializer.data)
            # Add categories to paginated response
            paginated_response.data['categories'] = categories_data
            return paginated_response
        
        # Non-paginated response
        tickets_serializer = self.get_serializer(queryset, many=True)
        return Response({
            'tickets': tickets_serializer.data,
            'categories': categories_data
        })
    
    @swagger_auto_schema(
        tags=["Support"],
        operation_summary="Create ticket",
        operation_description="Create a new support ticket with optional initial message",
        request_body=TicketCreateSerializer
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save(user=request.user)
            return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        tags=["Support"],
        operation_summary="Get ticket details",
        operation_description="Get detailed information about a specific ticket including all messages"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=["Support"],
        operation_summary="Manage ticket",
        operation_description="Multi-purpose endpoint: Add message, change status, or update priority in one request. Users cannot add messages to resolved or closed tickets.",
        request_body=TicketManageSerializer,
        consumes=['application/json', 'multipart/form-data']
    )
    @action(detail=True, methods=['post'], url_path='manage')
    def manage_ticket(self, request, pk=None):
        """Combined endpoint for managing tickets - add messages, change status, update priority"""
        ticket = self.get_object()
        serializer = TicketManageSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        response_data = {}
        
        # Check if user is trying to add a message
        message_text = data.get('message')
        if message_text:
            # Check if ticket is resolved or closed and user is not staff
            if ticket.status in ['resolved', 'closed'] and not request.user.is_staff:
                return Response(
                    {
                        "error": f"Cannot add messages to {ticket.status} tickets. Please create a new ticket if you need further assistance."
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Staff can always add messages, even to closed/resolved tickets
            message = TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_text,
                attachment=data.get('attachment'),
                is_internal=False
            )
            response_data['message_added'] = TicketMessageSerializer(message).data
            
            # If ticket was closed and user adds message, reopen it (only for regular users)
            # Staff messages don't automatically reopen tickets
            if ticket.status == 'closed' and not request.user.is_staff:
                ticket.status = 'open'
                ticket.save()
                response_data['status_changed'] = 'Ticket reopened due to new message'
        
        # Update ticket properties
        updated_fields = []
        
        # Priority can be changed by anyone (if ticket is not closed/resolved for regular users)
        new_priority = data.get('priority')
        if new_priority:
            if ticket.status in ['resolved', 'closed'] and not request.user.is_staff:
                return Response(
                    {
                        "error": f"Cannot modify {ticket.status} tickets. Please create a new ticket if you need further assistance."
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )
            ticket.priority = new_priority
            updated_fields.append('priority')
        
        # Status and assignment can only be changed by staff
        if request.user.is_staff:
            new_status = data.get('status')
            if new_status:
                old_status = ticket.status
                ticket.status = new_status
                updated_fields.append('status')
                
                if new_status == 'resolved' and old_status != 'resolved':
                    ticket.resolved_at = timezone.now()
                elif new_status != 'resolved':
                    ticket.resolved_at = None
            
            assigned_to_id = data.get('assigned_to')
            if assigned_to_id is not None:
                if assigned_to_id == 0:  # Unassign
                    ticket.assigned_to = None
                    updated_fields.append('assigned_to')
                else:
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        assignee = User.objects.get(id=assigned_to_id, is_staff=True)
                        ticket.assigned_to = assignee
                        updated_fields.append('assigned_to')
                    except User.DoesNotExist:
                        return Response(
                            {"error": "Invalid staff member ID"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
        
        # Save changes if any
        if updated_fields:
            ticket.save()
            response_data['updated_fields'] = updated_fields
        
        # Return updated ticket data
        response_data['ticket'] = TicketSerializer(ticket).data
        
        return Response(response_data)