from django.db import models
from django.contrib.auth.models import User
import json
from django.conf import settings

class Product(models.Model):
    msku = models.CharField(max_length=200, unique=True, primary_key=True)
    product_name = models.CharField(max_length=500)
    opening_stock = models.IntegerField(default=0)
    buffer_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product_name} ({self.msku})"

class WarehouseLocation(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class ProductStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(WarehouseLocation, on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['product', 'warehouse']

class SKUMapping(models.Model):
    sku = models.CharField(max_length=200)
    msku = models.CharField(max_length=200)
    marketplace = models.CharField(max_length=50)
    product_title = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['sku', 'marketplace']
    
    def __str__(self):
        return f"{self.sku} -> {self.msku}"

class SalesOrder(models.Model):
    ORDER_STATES = [
        ('DELIVERED', 'Delivered'),
        ('SHIPPED', 'Shipped'),
        ('RETURN_REQUESTED', 'Return Requested'),
        ('RTO_INITIATED', 'RTO Initiated'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_id = models.CharField(max_length=100)
    order_date = models.DateField()
    sku = models.CharField(max_length=200)
    msku = models.CharField(max_length=200, blank=True)
    product_name = models.TextField()
    quantity = models.IntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_state = models.CharField(max_length=20, choices=ORDER_STATES)
    customer_state = models.CharField(max_length=50, blank=True)
    marketplace = models.CharField(max_length=50)
    warehouse_code = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DataUpload(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/')
    upload_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    records_processed = models.IntegerField(default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,
    null=True,
    blank=True
)