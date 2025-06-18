import re
from django.db.models import Sum, Count, Avg
from .models import SalesOrder, Product, ProductStock
from datetime import datetime, timedelta
import pandas as pd

class AIQueryProcessor:
    def __init__(self):
        self.intent_patterns = {
            'top_products': [
                r'top\s+(?:selling\s+)?products?',
                r'best\s+(?:selling\s+)?products?',
                r'most\s+(?:popular\s+)?products?'
            ],
            'sales_summary': [
                r'total\s+sales?',
                r'sales?\s+summary',
                r'revenue',
                r'how\s+much\s+(?:did\s+we\s+)?(?:sell|sold|make)'
            ],
            'stock_status': [
                r'stock\s+(?:levels?|status)',
                r'inventory',
                r'how\s+much\s+stock',
                r'stock\s+remaining'
            ],
            'order_status': [
                r'orders?\s+(?:by\s+)?status',
                r'delivered\s+orders?',
                r'pending\s+orders?',
                r'returned?\s+orders?'
            ],
            'marketplace_analysis': [
                r'(?:sales?\s+)?(?:by\s+)?marketplace',
                r'amazon\s+(?:vs\s+)?flipkart',
                r'which\s+marketplace'
            ]
        }
    
    def detect_intent(self, query):
        """Detect user intent from query"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return 'general'
    
    def extract_timeframe(self, query):
        """Extract timeframe from query"""
        query_lower = query.lower()
        today = datetime.now().date()
        
        if 'today' in query_lower:
            return today, today
        elif 'yesterday' in query_lower:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif 'this week' in query_lower:
            start_week = today - timedelta(days=today.weekday())
            return start_week, today
        elif 'this month' in query_lower:
            start_month = today.replace(day=1)
            return start_month, today
        elif 'last month' in query_lower:
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start, last_month_end
        else:
            # Default to last 30 days
            start_date = today - timedelta(days=30)
            return start_date, today
    
    def process_query(self, query):
        """Process natural language query and return results"""
        intent = self.detect_intent(query)
        start_date, end_date = self.extract_timeframe(query)
        
        # Filter orders by date range
        orders = SalesOrder.objects.filter(
            order_date__range=[start_date, end_date]
        )
        
        if intent == 'top_products':
            return self.get_top_products(orders, query)
        elif intent == 'sales_summary':
            return self.get_sales_summary(orders, query)
        elif intent == 'stock_status':
            return self.get_stock_status(query)
        elif intent == 'order_status':
            return self.get_order_status(orders, query)
        elif intent == 'marketplace_analysis':
            return self.get_marketplace_analysis(orders, query)
        else:
            return self.get_general_insights(orders, query)
    
    def get_top_products(self, orders, query):
        """Get top selling products"""
        top_products = orders.values('msku', 'product_name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('selling_price'),
            order_count=Count('id')
        ).order_by('-total_quantity')[:10]
        
        response = "Here are your top selling products:\n\n"
        for i, product in enumerate(top_products, 1):
            response += f"{i}. {product['product_name'][:50]}...\n"
            response += f"   - Quantity Sold: {product['total_quantity']}\n"
            response += f"   - Revenue: ₹{product['total_revenue']:,.2f}\n"
            response += f"   - Orders: {product['order_count']}\n\n"
        
        return {
            'response': response,
            'data': list(top_products),
            'chart_type': 'bar',
            'chart_data': {
                'labels': [p['product_name'][:30] for p in top_products],
                'values': [p['total_quantity'] for p in top_products]
            }
        }
    
    def get_sales_summary(self, orders, query):
        """Get sales summary"""
        summary = orders.aggregate(
            total_orders=Count('id'),
            total_quantity=Sum('quantity'),
            total_revenue=Sum('selling_price'),
            avg_order_value=Avg('selling_price')
        )
        
        response = f"""Sales Summary:

Total Orders: {summary['total_orders']:,}
Total Quantity Sold: {summary['total_quantity']:,}
Total Revenue: ₹{summary['total_revenue']:,.2f}
Average Order Value: ₹{summary['avg_order_value']:.2f}

"""
        
        # Daily sales trend
        daily_sales = orders.values('order_date').annotate(
            daily_revenue=Sum('selling_price'),
            daily_orders=Count('id')
        ).order_by('order_date')
        
        return {
            'response': response,
            'data': summary,
            'chart_type': 'line',
            'chart_data': {
                'labels': [str(d['order_date']) for d in daily_sales],
                'values': [float(d['daily_revenue'] or 0) for d in daily_sales]
            }
        }
    
    def get_stock_status(self, query):
        """Get current stock status"""
        stock_data = ProductStock.objects.select_related('product').values(
            'product__msku',
            'product__product_name',
            'warehouse__code'
        ).annotate(
            total_stock=Sum('stock_quantity')
        ).order_by('-total_stock')[:15]
        
        response = "Current Stock Status:\n\n"
        for stock in stock_data:
            response += f"• {stock['product__product_name'][:40]}...\n"
            response += f"  Stock: {stock['total_stock']} units\n"
            response += f"  Warehouse: {stock['warehouse__code']}\n\n"
        
        return {
            'response': response,
            'data': list(stock_data),
            'chart_type': 'pie',
            'chart_data': {
                'labels': [s['product__msku'] for s in stock_data],
                'values': [s['total_stock'] for s in stock_data]
            }
        }
    
    def get_order_status(self, orders, query):
        """Get order status analysis"""
        status_data = orders.values('order_state').annotate(
            count=Count('id'),
            revenue=Sum('selling_price')
        ).order_by('-count')
        
        response = "Order Status Breakdown:\n\n"
        for status in status_data:
            response += f"• {status['order_state']}: {status['count']} orders\n"
            response += f"  Revenue: ₹{status['revenue']:,.2f}\n\n"
        
        return {
            'response': response,
            'data': list(status_data),
            'chart_type': 'doughnut',
            'chart_data': {
                'labels': [s['order_state'] for s in status_data],
                'values': [s['count'] for s in status_data]
            }
        }
    
    def get_marketplace_analysis(self, orders, query):
        """Get marketplace performance analysis"""
        marketplace_data = orders.values('marketplace').annotate(
            total_orders=Count('id'),
            total_revenue=Sum('selling_price'),
            avg_order_value=Avg('selling_price')
        ).order_by('-total_revenue')
        
        response = "Marketplace Performance:\n\n"
        for mp in marketplace_data:
            response += f"• {mp['marketplace'].title()}:\n"
            response += f"  Orders: {mp['total_orders']:,}\n"
            response += f"  Revenue: ₹{mp['total_revenue']:,.2f}\n"
            response += f"  Avg Order Value: ₹{mp['avg_order_value']:.2f}\n\n"
        
        return {
            'response': response,
            'data': list(marketplace_data),
            'chart_type': 'bar',
            'chart_data': {
                'labels': [mp['marketplace'].title() for mp in marketplace_data],
                'values': [float(mp['total_revenue'] or 0) for mp in marketplace_data]
            }
        }
    
    def get_general_insights(self, orders, query):
        """Get general insights"""
        total_orders = orders.count()
        total_revenue = orders.aggregate(Sum('selling_price'))['selling_price__sum'] or 0
        
        response = f"""General Insights:

I found {total_orders:,} orders with total revenue of ₹{total_revenue:,.2f}.

You can ask me more specific questions like:
• "Show me top selling products this month"
• "What's our total sales this week?"
• "Which marketplace is performing better?"
• "Show me current stock levels"
• "How many orders are delivered vs returned?"
"""
        
        return {
            'response': response,
            'data': {'total_orders': total_orders, 'total_revenue': total_revenue},
            'chart_type': None,
            'chart_data': None
        }