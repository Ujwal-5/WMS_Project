from django.contrib import admin
from .models import *

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['msku', 'product_name', 'opening_stock', 'buffer_stock']
    search_fields = ['msku', 'product_name']
    list_filter = ['created_at']

@admin.register(WarehouseLocation)
class WarehouseLocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']

@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'stock_quantity']
    list_filter = ['warehouse']

@admin.register(SKUMapping)
class SKUMappingAdmin(admin.ModelAdmin):
    list_display = ['sku', 'msku', 'marketplace', 'created_at']
    list_filter = ['marketplace', 'created_at']
    search_fields = ['sku', 'msku']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'order_date', 'sku', 'msku', 'quantity', 'order_state', 'marketplace']
    list_filter = ['order_state', 'marketplace', 'order_date']
    search_fields = ['order_id', 'sku', 'msku', 'product_name']

@admin.register(DataUpload)
class DataUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'upload_date', 'processed', 'records_processed', 'user']
    list_filter = ['processed', 'upload_date']