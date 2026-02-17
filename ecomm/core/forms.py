from django import forms

from core.models import ProductReview,ReturnRequest


class ProductReviewForm(forms.ModelForm):
    review = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Write review"}))

    class Meta:
        model = ProductReview
        fields = ['review', 'rating']

class ReturnRequestForm(forms.ModelForm):
    """Form for customers to request a return"""
    
    # Custom reason field (you can replace with choices from ReturnReason model)
    REASON_CHOICES = [
        ('', '-- Select a reason --'),
        ('wrong_size_small', 'Wrong size - too small'),
        ('wrong_size_big', 'Wrong size - too big'),
        ('defective', 'Defective/Damaged item'),
        ('wrong_item', 'Wrong item received'),
        ('changed_mind', 'Changed mind / No longer needed'),
        ('quality', 'Quality not as expected'),
        ('arrived_late', 'Arrived too late'),
        ('better_price', 'Found better price elsewhere'),
        ('other', 'Other reason'),
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'reason_select'}),
        required=True
    )
    
    reason_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': 'Please provide more details about your return request...'
        }),
        required=False,
        help_text="Optional: Provide additional details"
    )
    
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'id': 'quantity_input'
        }),
        required=True,
        help_text="Enter quantity to return"
    )
    
    # Hidden field for other reason (shown via JavaScript)
    other_reason_text = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'other_reason_text',
            'placeholder': 'Please specify your reason'
        }),
        required=False
    )
    
    class Meta:
        model = ReturnRequest
        fields = ['reason', 'reason_details', 'quantity']
    
    def __init__(self, *args, **kwargs):
        self.order_item = kwargs.pop('order_item', None)
        super().__init__(*args, **kwargs)
        
        if self.order_item:
            # Set max quantity based on order item
            self.fields['quantity'].widget.attrs['max'] = self.order_item.qty
            self.fields['quantity'].widget.attrs['value'] = 1
            self.fields['quantity'].help_text = f"Maximum: {self.order_item.qty} (you ordered {self.order_item.qty})"
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.order_item and quantity > self.order_item.qty:
            raise forms.ValidationError(
                f"Cannot return more than {self.order_item.qty} items. You only ordered {self.order_item.qty}."
            )
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity
    
    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        other_reason = cleaned_data.get('other_reason_text')
        
        # If reason is 'other', require the other_reason_text
        if reason == 'other' and not other_reason:
            self.add_error('other_reason_text', 'Please specify your reason')
        
        return cleaned_data