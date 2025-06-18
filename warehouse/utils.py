import pandas as pd
import re
from datetime import datetime
from .models import SKUMapping, Product, SalesOrder, WarehouseLocation, ProductStock
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class SKUMapper:
    def __init__(self):
        self.mappings = {}
        self.load_mappings()
    
    def load_mappings(self):
        """Load existing SKU mappings from database"""
        mappings = SKUMapping.objects.all()
        for mapping in mappings:
            key = f"{mapping.sku}_{mapping.marketplace}"
            self.mappings[key] = mapping.msku
    
    def find_msku(self, sku, marketplace, product_title=""):
        """Find MSKU for given SKU"""
        key = f"{sku}_{marketplace}"
        
        # Check exact match first
        if key in self.mappings:
            return self.mappings[key]
        
        # Try fuzzy matching based on product title
        if product_title:
            return self.fuzzy_match(sku, marketplace, product_title)
        
        return None
    
    def fuzzy_match(self, sku, marketplace, product_title):
        """Attempt fuzzy matching based on product characteristics"""
        # Simple fuzzy matching logic
        title_lower = product_title.lower()
        
        # Extract common product identifiers
        if 'music box' in title_lower:
            if 'harry potter' in title_lower:
                return 'f_ay hp M box black'
            elif 'money heist' in title_lower or 'bella ciao' in title_lower:
                return 'MONEY HEIST A-8_BROWN'
            elif 'sunshine' in title_lower:
                return 'MB_YouAreSunshine_Blk'
        
        elif 'breathing' in title_lower:
            if 'dog' in title_lower:
                return 'CSTE_0545_ST_Animal_Breathing_Dog_B_2'
            elif 'stitch' in title_lower:
                return 'Breathing_Lilo_Stich_Blue'
        
        elif 'pillow' in title_lower:
            if 'chimmy' in title_lower:
                return 'CSTE_0001_ST_Bts_Pillow_Chimmy'
            elif 'tata' in title_lower:
                return 'CSTE_0002_ST_Bts_Pillow_Tata'
        
        return None
    
    def add_mapping(self, sku, msku, marketplace, product_title=""):
        """Add new SKU mapping"""
        mapping, created = SKUMapping.objects.get_or_create(
            sku=sku,
            marketplace=marketplace,
            defaults={
                'msku': msku,
                'product_title': product_title
            }
        )
        
        key = f"{sku}_{marketplace}"
        self.mappings[key] = msku
        
        return mapping

class DataProcessor:
    def __init__(self):
        self.sku_mapper = SKUMapper()
    
    def detect_format(self, df):
        """Auto-detect data format based on column names"""
        columns = [col.lower() for col in df.columns]
        
        if 'fnsku' in columns or 'asin' in columns:
            return 'amazon'
        elif 'fsn' in columns or 'order item id' in columns:
            return 'flipkart'
        elif 'sub order no' in columns and 'reason for credit entry' in columns:
            return 'meesho'
        else:
            return 'unknown'
    
    def process_amazon_data(self, df):
        """Process Amazon sales data"""
        processed_data = []
        
        for _, row in df.iterrows():
            try:
                order_date = pd.to_datetime(row['Date']).date()
                msku = row.get('MSKU', '')
                
                if not msku:
                    msku = self.sku_mapper.find_msku(
                        row.get('FNSKU', ''),
                        'amazon',
                        row.get('Title', '')
                    )
                
                processed_data.append({
                    'order_id': row.get('Reference ID', ''),
                    'order_date': order_date,
                    'sku': row.get('FNSKU', ''),
                    'msku': msku or '',
                    'product_name': row.get('Title', ''),
                    'quantity': abs(int(row.get('Quantity', 0))),
                    'selling_price': 0,  # Not available in this format
                    'order_state': 'DELIVERED',
                    'customer_state': '',
                    'marketplace': 'amazon',
                    'warehouse_code': row.get('Fulfillment Center', ''),
                })
            except Exception as e:
                logger.error(f"Error processing Amazon row: {e}")
                continue
        
        return processed_data
    
    def process_flipkart_data(self, df):
        """Process Flipkart sales data"""
        processed_data = []
        
        for _, row in df.iterrows():
            try:
                order_date = pd.to_datetime(row['Ordered On']).date()
                sku = row.get('SKU', '')
                
                msku = self.sku_mapper.find_msku(
                    sku,
                    'flipkart',
                    row.get('Product', '')
                )
                
                processed_data.append({
                    'order_id': row.get('Order Id', ''),
                    'order_date': order_date,
                    'sku': sku,
                    'msku': msku or '',
                    'product_name': row.get('Product', ''),
                    'quantity': int(row.get('Quantity', 0)),
                    'selling_price': float(row.get('Selling Price Per Item', 0)),
                    'order_state': row.get('Order State', '').upper(),
                    'customer_state': row.get('State', ''),
                    'marketplace': 'flipkart',
                    'warehouse_code': '',
                })
            except Exception as e:
                logger.error(f"Error processing Flipkart row: {e}")
                continue
        
        return processed_data
    
    def process_meesho_data(self, df):
        """Process Meesho sales data"""
        processed_data = []
        
        for _, row in df.iterrows():
            try:
                order_date = pd.to_datetime(row['Order Date']).date()
                sku = row.get('SKU', '')
                
                msku = self.sku_mapper.find_msku(
                    sku,
                    'meesho',
                    row.get('Product Name', '')
                )
                
                processed_data.append({
                    'order_id': row.get('Sub Order No', ''),
                    'order_date': order_date,
                    'sku': sku,
                    'msku': msku or '',
                    'product_name': row.get('Product Name', ''),
                    'quantity': int(row.get('Quantity', 0)),
                    'selling_price': float(row.get('Supplier Discounted Price (Incl GST and Commision)', 0)),
                    'order_state': row.get('Reason for Credit Entry', '').upper(),
                    'customer_state': row.get('Customer State', ''),
                    'marketplace': 'meesho',
                    'warehouse_code': '',
                })
            except Exception as e:
                logger.error(f"Error processing Meesho row: {e}")
                continue
        
        return processed_data
    
    def process_file(self, file_path, data_format='auto'):
        """Process uploaded file and return processed data"""
        try:
            # Read file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Auto-detect format if needed
            if data_format == 'auto':
                data_format = self.detect_format(df)
            
            # Process based on format
            if data_format == 'amazon':
                return self.process_amazon_data(df)
            elif data_format == 'flipkart':
                return self.process_flipkart_data(df)
            elif data_format == 'meesho':
                return self.process_meesho_data(df)
            else:
                raise ValueError(f"Unknown data format: {data_format}")
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    def save_to_database(self, processed_data):
        """Save processed data to database"""
        with transaction.atomic():
            saved_count = 0
            for data in processed_data:
                try:
                    # Create or update sales order
                    order, created = SalesOrder.objects.get_or_create(
                        order_id=data['order_id'],
                        sku=data['sku'],
                        defaults=data
                    )
                    
                    if created:
                        saved_count += 1
                        
                        # Update stock if MSKU is mapped
                        if data['msku']:
                            self.update_stock(data['msku'], data['quantity'], data['warehouse_code'])
                
                except Exception as e:
                    logger.error(f"Error saving order data: {e}")
                    continue
            
            return saved_count
    
    def update_stock(self, msku, quantity, warehouse_code):
        """Update product stock based on sales"""
        try:
            product, _ = Product.objects.get_or_create(
                msku=msku,
                defaults={'product_name': f'Product {msku}', 'opening_stock': 0}
            )
            
            warehouse, _ = WarehouseLocation.objects.get_or_create(
                code=warehouse_code or 'DEFAULT',
                defaults={'name': f'Warehouse {warehouse_code}'}
            )
            
            stock, _ = ProductStock.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                defaults={'stock_quantity': 0}
            )
            
            # Reduce stock for sales
            stock.stock_quantity = max(0, stock.stock_quantity - quantity)
            stock.save()
            
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
