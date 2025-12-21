from core.models import Product, Category, SubCategory, MiniSubCategory
from django import forms

class AddProductForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Product Title", "class":"form-control"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Product Description", "class":"form-control"}))
    price = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "Sale Price", "class":"form-control"}))
    old_price = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "Old Price", "class":"form-control"}))
    type = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Type of product e.g organic cream", "class":"form-control"}))
    stock_count = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "How many are in stock?", "class":"form-control"}))
    life = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "How long would this product live?", "class":"form-control"}))
    mfd = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control"
            })
    )
    image = forms.ImageField(widget=forms.FileInput(attrs={"class":"form-control"}))
    
    class Meta:
        model = Product
        fields = [
            'title',
            'image',
            'description',
            'price',
            'old_price',
            'specifications',
            'type',
            'stock_count',
            'life',
            'mfd',
            'digital',
            'mini_subcategory',
        ]
        widgets = {
            'mini_subcategory': forms.Select(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Product specifications', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organize mini subcategories by their hierarchy for better UX
        self.fields['mini_subcategory'].queryset = MiniSubCategory.objects.all().select_related('subcategory__category')
        self.fields['mini_subcategory'].label_from_instance = lambda obj: f"{obj.subcategory.category.title} > {obj.subcategory.title} > {obj.title}"
        self.fields['mini_subcategory'].empty_label = "Select Category"