from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, TicketCategoryViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='tickets')
router.register(r'categories', TicketCategoryViewSet, basename='categories')

urlpatterns = [
    path('', include(router.urls)),
]