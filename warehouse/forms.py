from django import forms
from .models import SKUMapping, Product

class FileUploadForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    data_format = forms.ChoiceField(
        choices=[
            ('auto', 'Auto Detect'),
            ('amazon', 'Amazon Format'),
            ('flipkart', 'Flipkart Format'),
            ('meesho', 'Meesho Format'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class SKUMappingForm(forms.ModelForm):
    class Meta:
        model = SKUMapping
        fields = ['sku', 'msku', 'marketplace', 'product_title']
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'msku': forms.TextInput(attrs={'class': 'form-control'}),
            'marketplace': forms.TextInput(attrs={'class': 'form-control'}),
            'product_title': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class QueryForm(forms.Form):
    query = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ask me anything about your sales data... e.g., "Show me top selling products this month"'
        })
    )