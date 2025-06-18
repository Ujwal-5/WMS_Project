from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from .models import *
from .forms import *
from .utils import DataProcessor
from .ai_query import AIQueryProcessor
import json
import os
import plotly.graph_objects as go
import plotly.utils

def dashboard(request):
    """Main dashboard view"""
    # Get summary statistics
    total_products = Product.objects.count()
    total_orders = SalesOrder.objects.count()
    total_stock = ProductStock.objects.aggregate(Sum('stock_quantity'))['stock_quantity__sum'] or 0
    unmapped_skus = SalesOrder.objects.filter(msku='').count()
    
    # Get recent orders
    recent_orders = SalesOrder.objects.order_by('-created_at')[:10]
    
    # Get top products
    top_products = SalesOrder.objects.values('msku', 'product_name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Get marketplace distribution
    marketplace_data = SalesOrder.objects.values('marketplace').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Create charts
    charts = {}
    
    # Top products chart
    if top_products:
        fig_products = go.Figure(data=[
            go.Bar(
                x=[p['msku'][:20] for p in top_products],
                y=[p['total_sold'] for p in top_products],
                marker_color='#3498db'
            )
        ])
        fig_products.update_layout(
            title="Top 5 Products by Sales",
            xaxis_title="Product MSKU",
            yaxis_title="Quantity Sold",
            height=400
        )
        charts['top_products'] = json.dumps(fig_products, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Marketplace distribution chart
    if marketplace_data:
        fig_marketplace = go.Figure(data=[
            go.Pie(
                labels=[m['marketplace'].title() for m in marketplace_data],
                values=[m['count'] for m in marketplace_data],
                hole=0.4
            )
        ])
        fig_marketplace.update_layout(
            title="Orders by Marketplace",
            height=400
        )
        charts['marketplace'] = json.dumps(fig_marketplace, cls=plotly.utils.PlotlyJSONEncoder)
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_stock': total_stock,
        'unmapped_skus': unmapped_skus,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'marketplace_data': marketplace_data,
        'charts': charts,
    }
    
    return render(request, 'warehouse/dashboard.html', context)

def upload_data(request):
    """Handle file uploads and data processing"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save uploaded file
                uploaded_file = request.FILES['file']
                data_upload = DataUpload(
                    file_name=uploaded_file.name,
                    file_path=uploaded_file,
                    user=request.user if request.user.is_authenticated else None
                )
                data_upload.save()
                print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
                # Process the file
                processor = DataProcessor()
                file_path = data_upload.file_path.path
                data_format = form.cleaned_data['data_format']
                print('data_format',data_format)
                processed_data = processor.process_file(file_path, data_format)
                saved_count = processor.save_to_database(processed_data)
                
                # Update upload record
                data_upload.processed = True
                data_upload.records_processed = saved_count
                data_upload.save()
                
                messages.success(
                    request, 
                    f'Successfully processed {saved_count} records from {uploaded_file.name}'
                )
                
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = FileUploadForm()
    
    return render(request, 'warehouse/upload.html', {'form': form})

def sku_mapping(request):
    """Manage SKU to MSKU mappings"""
    if request.method == 'POST':
        form = SKUMappingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'SKU mapping added successfully!')
            return redirect('sku_mapping')
    else:
        form = SKUMappingForm()
    
    # Get existing mappings with pagination
    mappings = SKUMapping.objects.all().order_by('-created_at')
    paginator = Paginator(mappings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unmapped SKUs
    unmapped_orders = SalesOrder.objects.filter(msku='').values(
        'sku', 'marketplace', 'product_name'
    ).distinct()[:50]
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'unmapped_orders': unmapped_orders,
    }
    
    return render(request, 'warehouse/sku_mapping.html', context)

@csrf_exempt
def ai_query(request):
    """Handle AI-powered queries"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            if not query:
                return JsonResponse({'error': 'Query is required'}, status=400)
            
            # Process query with AI
            processor = AIQueryProcessor()
            result = processor.process_query(query)
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show query interface
    form = QueryForm()
    return render(request, 'warehouse/ai_query.html', {'form': form})

def inventory_view(request):
    """View current inventory status"""
    # Get all products with stock information
    products = Product.objects.prefetch_related('productstock_set__warehouse').all()
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(msku__icontains=search) | Q(product_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_products = products.count()
    total_stock = ProductStock.objects.aggregate(Sum('stock_quantity'))['stock_quantity__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_products': total_products,
        'total_stock': total_stock,
    }
    
    return render(request, 'warehouse/inventory.html', context)

def orders_view(request):
    """View all orders with filtering"""
    orders = SalesOrder.objects.all().order_by('-order_date')
    
    # Filtering
    marketplace = request.GET.get('marketplace', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if marketplace:
        orders = orders.filter(marketplace=marketplace)
    if status:
        orders = orders.filter(order_state=status)
    if search:
        orders = orders.filter(
            Q(order_id__icontains=search) | 
            Q(product_name__icontains=search) |
            Q(sku__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(orders, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    marketplaces = SalesOrder.objects.values_list('marketplace', flat=True).distinct()
    statuses = SalesOrder.objects.values_list('order_state', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'marketplaces': marketplaces,
        'statuses': statuses,
        'current_marketplace': marketplace,
        'current_status': status,
        'search': search,
    }
    
    return render(request, 'warehouse/orders.html', context)

def analytics_view(request):
    """Advanced analytics and reporting"""
    # Sales trend over time
    from django.db.models import DateField
    from django.db.models.functions import TruncDate
    
    daily_sales = SalesOrder.objects.annotate(
        date=TruncDate('order_date')
    ).values('date').annotate(
        total_orders=Count('id'),
        total_revenue=Sum('selling_price')
    ).order_by('date')
    
    # Create sales trend chart
    if daily_sales:
        fig_trend = go.Figure()
        
        dates = [item['date'] for item in daily_sales]
        orders = [item['total_orders'] for item in daily_sales]
        revenue = [float(item['total_revenue'] or 0) for item in daily_sales]
        
        fig_trend.add_trace(go.Scatter(
            x=dates, y=orders,
            mode='lines+markers',
            name='Orders',
            yaxis='y'
        ))
        
        fig_trend.add_trace(go.Scatter(
            x=dates, y=revenue,
            mode='lines+markers',
            name='Revenue',
            yaxis='y2'
        ))
        
        fig_trend.update_layout(
            title='Sales Trend Over Time',
            xaxis_title='Date',
            yaxis=dict(title='Number of Orders'),
            yaxis2=dict(title='Revenue (₹)', overlaying='y', side='right'),
            height=500
        )
        
        sales_trend_chart = json.dumps(fig_trend, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        sales_trend_chart = None
    
    # Top products by revenue
    top_revenue_products = SalesOrder.objects.values('msku', 'product_name').annotate(
        total_revenue=Sum('selling_price')
    ).order_by('-total_revenue')[:10]
    
    if top_revenue_products:
        fig_revenue = go.Figure(data=[
            go.Bar(
                x=[p['msku'][:20] for p in top_revenue_products],
                y=[float(p['total_revenue'] or 0) for p in top_revenue_products],
                marker_color='#2ecc71'
            )
        ])
        fig_revenue.update_layout(
            title="Top Products by Revenue",
            xaxis_title="Product MSKU",
            yaxis_title="Revenue (₹)",
            height=400
        )
        revenue_chart = json.dumps(fig_revenue, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        revenue_chart = None
    
    context = {
        'sales_trend_chart': sales_trend_chart,
        'revenue_chart': revenue_chart,
        'daily_sales': daily_sales,
        'top_revenue_products': top_revenue_products,
    }
    
    return render(request, 'warehouse/analytics.html', context)