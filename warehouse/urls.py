from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.upload_data, name='upload_data'),
    path('sku-mapping/', views.sku_mapping, name='sku_mapping'),
    path('ai-query/', views.ai_query, name='ai_query'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('orders/', views.orders_view, name='orders'),
    path('analytics/', views.analytics_view, name='analytics'),
]