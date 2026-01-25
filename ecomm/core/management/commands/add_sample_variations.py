from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Color, Size

class Command(BaseCommand):
    help = 'Add sample colors and sizes for product variations'
    
    def handle(self, *args, **kwargs):
        # Sample colors with common hex codes
        colors = [
            {'name': 'Red', 'hex_code': '#FF0000'},
            {'name': 'Blue', 'hex_code': '#0000FF'},
            {'name': 'Green', 'hex_code': '#00FF00'},
            {'name': 'Black', 'hex_code': '#000000'},
            {'name': 'White', 'hex_code': '#FFFFFF'},
            {'name': 'Gray', 'hex_code': '#808080'},
            {'name': 'Silver', 'hex_code': '#C0C0C0'},
            {'name': 'Gold', 'hex_code': '#FFD700'},
            {'name': 'Navy Blue', 'hex_code': '#000080'},
            {'name': 'Brown', 'hex_code': '#A52A2A'},
            {'name': 'Beige', 'hex_code': '#F5F5DC'},
            {'name': 'Pink', 'hex_code': '#FFC0CB'},
            {'name': 'Purple', 'hex_code': '#800080'},
            {'name': 'Orange', 'hex_code': '#FFA500'},
            {'name': 'Yellow', 'hex_code': '#FFFF00'},
            {'name': 'Teal', 'hex_code': '#008080'},
            {'name': 'Maroon', 'hex_code': '#800000'},
            {'name': 'Olive', 'hex_code': '#808000'},
            {'name': 'Lavender', 'hex_code': '#E6E6FA'},
            {'name': 'Cyan', 'hex_code': '#00FFFF'},
        ]
        
        # Sample sizes for different product types
        clothing_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
        shoe_sizes = ['6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10', '10.5', '11', '12', '13']
        pants_sizes = ['28', '30', '32', '34', '36', '38', '40', '42', '44']
        generic_sizes = ['One Size', 'Small', 'Medium', 'Large', 'Extra Large']
        
        all_sizes = clothing_sizes + shoe_sizes + pants_sizes + generic_sizes
        
        # Counter for tracking
        colors_created = 0
        sizes_created = 0
        
        # Create colors
        self.stdout.write("Creating colors...")
        for color_data in colors:
            color, created = Color.objects.get_or_create(
                name=color_data['name'],
                defaults={'hex_code': color_data['hex_code']}
            )
            if created:
                colors_created += 1
                self.stdout.write(f'   Created color: {color.name} ({color.hex_code})')
        
        # Create sizes
        self.stdout.write("\n Creating sizes...")
        for size_name in all_sizes:
            size, created = Size.objects.get_or_create(name=size_name)
            if created:
                sizes_created += 1
                self.stdout.write(f'  Created size: {size.name}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n Successfully created {colors_created} colors and {sizes_created} sizes!\n'
        ))
        self.stdout.write(
            f'Total colors in database: {Color.objects.count()}\n'
            f'Total sizes in database: {Size.objects.count()}'
        )