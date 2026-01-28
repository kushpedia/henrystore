from core.models import Product, Category, SubCategory, MiniSubCategory,Color, Size, ProductVariation
from django import forms
class AddProductForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Product Title", "class":"form-control"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Product Description", "class":"form-control"}))
    price = forms.DecimalField(widget=forms.NumberInput(attrs={'placeholder': "Sale Price", "class":"form-control"}))
    old_price = forms.DecimalField(widget=forms.NumberInput(attrs={'placeholder': "Old Price", "class":"form-control"}))
    type = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Type of product e.g organic cream", "class":"form-control"}))
    stock_count = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': "How many are in stock?", "class":"form-control"}))
    image = forms.ImageField(widget=forms.FileInput(attrs={"class":"form-control"}))
    
    # Variation fields
    has_variations = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'has_variations_toggle'})
    )
    
    available_colors = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2-multiple', 'multiple': 'multiple'}),
        label="Available Colors"
    )
    
    available_sizes = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2-multiple', 'multiple': 'multiple'}),
        label="Available Sizes"
    )
    
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
            'digital',
            'mini_subcategory',
            'has_variations',
            'available_colors',
            'available_sizes',
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
    
    def clean(self):
        cleaned_data = super().clean()
        has_variations = cleaned_data.get('has_variations')
        
        if has_variations:
            # If variations are enabled, check if at least one color or size is selected
            available_colors = cleaned_data.get('available_colors')
            available_sizes = cleaned_data.get('available_sizes')
            
            if not available_colors and not available_sizes:
                raise forms.ValidationError(
                    "If variations are enabled, you must select at least one color or size."
                )
        
        return cleaned_data


# Form for individual variations (to be used in JavaScript)
class VariationForm(forms.ModelForm):
    class Meta:
        model = ProductVariation
        fields = ['color', 'size', 'price', 'old_price', 'stock_count', 'image']
        widgets = {
            'color': forms.Select(attrs={'class': 'form-control variation-color'}),
            'size': forms.Select(attrs={'class': 'form-control variation-size'}),
            'price': forms.NumberInput(attrs={'class': 'form-control variation-price', 'placeholder': 'Variation Price'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control variation-old-price', 'placeholder': 'Variation Old Price'}),
            'stock_count': forms.NumberInput(attrs={'class': 'form-control variation-stock', 'placeholder': 'Stock Count'}),
            'image': forms.FileInput(attrs={'class': 'form-control variation-image'}),
        }
    
    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        # Filter choices if product is provided
        if product:
            self.fields['color'].queryset = product.available_colors.all()
            self.fields['size'].queryset = product.available_sizes.all()