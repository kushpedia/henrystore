# management/commands/generate_sample_returns.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
from datetime import timedelta, datetime
from core.models import ReturnRequest, CartOrder, CartOrderItems

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample return requests for testing with dates spread across last 2 years'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of sample returns to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample returns before generating new ones'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            default='realistic',
            choices=['realistic', 'uniform', 'increasing', 'decreasing', 'seasonal'],
            help='Distribution pattern for returns (default: realistic)'
        )

    def handle(self, *args, **options):
        count = options['count']
        pattern = options['pattern']
        
        # Clear existing sample returns if requested
        if options['clear']:
            self.stdout.write('Clearing existing sample returns...')
            # Delete returns with sample flag in reason
            ReturnRequest.objects.filter(reason__icontains='Sample').delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing sample returns'))

        self.stdout.write(f'Generating {count} sample return requests spread across the last 2 years...')
        self.stdout.write(f'Using pattern: {pattern}')

        # Get or create test users
        users = self.get_or_create_test_users()
        
        # Get or create test orders and items
        orders_data = self.get_or_create_test_orders(users)
        
        # Calculate date range (last 2 years = 730 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        # Generate returns with dates spread across 2 years
        returns_created = 0
        
        # Generate dates based on pattern
        dates = self.generate_dates(count, pattern, start_date, end_date)
        
        for i, created_date in enumerate(dates):
            try:
                # Select random order and item
                order_item = random.choice(orders_data['order_items'])
                order = order_item.order
                user = order.user
                
                # Check if there's already an active return for this item
                existing_return = ReturnRequest.objects.filter(
                    order_item=order_item,
                    status__in=['pending', 'approved', 'received']
                ).exists()
                
                if existing_return:
                    # Try a different item up to 5 times
                    for _ in range(5):
                        order_item = random.choice(orders_data['order_items'])
                        order = order_item.order
                        user = order.user
                        existing_return = ReturnRequest.objects.filter(
                            order_item=order_item,
                            status__in=['pending', 'approved', 'received']
                        ).exists()
                        if not existing_return:
                            break
                    else:
                        # Skip if still can't find unique item
                        continue
                
                # Create return with this date
                return_request = self.create_sample_return(
                    order_item, order, user, i, created_date
                )
                returns_created += 1
                
                if returns_created % 10 == 0:
                    self.stdout.write(f'Created {returns_created} returns...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating return: {str(e)}'))
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {returns_created} sample return requests spread across the last 2 years')
        )
        
        # Show date distribution
        self.show_date_distribution()

    def generate_dates(self, count, pattern, start_date, end_date):
        """Generate random dates based on specified pattern"""
        dates = []
        total_days = 730  # 2 years
        
        if pattern == 'uniform':
            # Uniform distribution across 2 years
            for _ in range(count):
                random_days = random.randint(0, total_days)
                dates.append(end_date - timedelta(days=random_days))
                
        elif pattern == 'increasing':
            # More returns in recent months (increasing trend)
            for _ in range(count):
                # Using beta distribution with alpha > beta for increasing trend
                random_days = int(random.betavariate(3, 1.5) * total_days)
                dates.append(end_date - timedelta(days=random_days))
                
        elif pattern == 'decreasing':
            # More returns in older months (decreasing trend)
            for _ in range(count):
                # Using beta distribution with alpha < beta for decreasing trend
                random_days = int(random.betavariate(1.5, 3) * total_days)
                dates.append(end_date - timedelta(days=random_days))
                
        elif pattern == 'seasonal':
            # Seasonal pattern (more returns during certain months)
            for _ in range(count):
                # Generate random date
                random_days = random.randint(0, total_days)
                date = end_date - timedelta(days=random_days)
                
                # Weight by season (higher in Jan, Nov, Dec - after holidays)
                month = date.month
                if month in [11, 12, 1]:  # Holiday season
                    if random.random() < 0.3:  # 30% chance to keep
                        dates.append(date)
                elif month in [6, 7, 8]:  # Summer
                    if random.random() < 0.2:  # 20% chance to keep
                        dates.append(date)
                else:  # Other months
                    if random.random() < 0.1:  # 10% chance to keep
                        dates.append(date)
            
            # If we don't have enough dates, fill with uniform distribution
            while len(dates) < count:
                random_days = random.randint(0, total_days)
                dates.append(end_date - timedelta(days=random_days))
                
        else:  # realistic (default)
            # Realistic pattern: more recent, some seasonal spikes
            for _ in range(count):
                # Mix of distributions for realism
                rand_type = random.random()
                
                if rand_type < 0.5:  # 50% recent (last 6 months)
                    random_days = random.randint(0, 180)
                elif rand_type < 0.75:  # 25% medium (6-12 months)
                    random_days = random.randint(181, 365)
                else:  # 25% old (12-24 months)
                    random_days = random.randint(366, 730)
                
                date = end_date - timedelta(days=random_days)
                
                # Add seasonal variation
                month = date.month
                if month in [11, 12, 1] and random.random() < 0.7:  # Higher chance in holidays
                    dates.append(date)
                elif month in [6, 7, 8] and random.random() < 0.5:  # Medium chance in summer
                    dates.append(date)
                elif random.random() < 0.4:  # Lower chance other months
                    dates.append(date)
            
            # Ensure we have exactly count dates
            while len(dates) < count:
                random_days = random.randint(0, total_days)
                dates.append(end_date - timedelta(days=random_days))
        
        # Sort dates chronologically
        dates.sort()
        return dates

    def get_or_create_test_users(self):
        """Get or create test users"""
        users = []
        
        # Create some test customers if they don't exist
        test_users_data = [
            {'email': 'john.doe@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'email': 'jane.smith@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'email': 'bob.wilson@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
            {'email': 'alice.brown@example.com', 'first_name': 'Alice', 'last_name': 'Brown'},
            {'email': 'charlie.davis@example.com', 'first_name': 'Charlie', 'last_name': 'Davis'},
            {'email': 'emma.jones@example.com', 'first_name': 'Emma', 'last_name': 'Jones'},
            {'email': 'michael.lee@example.com', 'first_name': 'Michael', 'last_name': 'Lee'},
            {'email': 'sarah.williams@example.com', 'first_name': 'Sarah', 'last_name': 'Williams'},
            {'email': 'david.miller@example.com', 'first_name': 'David', 'last_name': 'Miller'},
            {'email': 'lisa.anderson@example.com', 'first_name': 'Lisa', 'last_name': 'Anderson'},
            {'email': 'kevin.taylor@example.com', 'first_name': 'Kevin', 'last_name': 'Taylor'},
            {'email': 'amanda.thomas@example.com', 'first_name': 'Amanda', 'last_name': 'Thomas'},
        ]
        
        for user_data in test_users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True
                }
            )
            if created:
                # Set a default password for test users
                user.set_password('testpass123')
                user.save()
            users.append(user)
        
        return users

    def get_or_create_test_orders(self, users):
        """Get or create test orders and items with dates spread across last 2 years"""
        
        if CartOrder.objects.exists():
            # Use existing orders
            orders = list(CartOrder.objects.all())
            order_items = list(CartOrderItems.objects.all())
            
            return {
                'orders': orders,
                'order_items': order_items
            }
        else:
            # Create sample orders if none exist
            self.stdout.write('No orders found. Creating sample orders...')
            return self.create_sample_orders(users)

    def create_sample_orders(self, users):
        """Create sample orders with dates spread across last 2 years"""
        orders = []
        order_items = []
        
        product_names = [
            'Classic T-Shirt', 'Slim Fit Jeans', 'Leather Wallet', 'Running Shoes',
            'Winter Jacket', 'Cotton Sweater', 'Denim Shirt', 'Casual Blazer',
            'Sports Cap', 'Wool Scarf', 'Leather Belt', 'Dress Shoes',
            'Summer Dress', 'Cargo Pants', 'Hoodie', 'Polo Shirt',
            'Swim Shorts', 'Yoga Pants', 'Backpack', 'Sunglasses',
            'Smart Watch', 'Wireless Earbuds', 'Phone Case', 'Laptop Sleeve',
            'Water Bottle', 'Gym Bag', 'Running Shorts', 'Baseball Cap',
            'Hiking Boots', 'Winter Gloves', 'Beanie Hat', 'Umbrella',
            'Travel Pillow', 'Luggage Set', 'Fitness Tracker', 'Bluetooth Speaker',
            'Coffee Mug', 'Desk Lamp', 'Notebook Set', 'Pen Set',
            'Wall Art', 'Photo Frame', 'Candle Set', 'Throw Pillow',
            'Bath Towel Set', 'Bed Sheets', 'Pillow Cases', 'Blanket'
        ]
        
        end_date = timezone.now()
        
        # Create orders spread across last 2 years
        for i in range(60):  # Create 60 sample orders
            user = random.choice(users)
            
            # Generate random date within last 2 years
            random_days = random.randint(0, 730)
            order_date = end_date - timedelta(days=random_days)
            
            # Status based on order age
            if random_days < 7:
                status = random.choice(['processing', 'shipped', 'delivered'])
            elif random_days < 30:
                status = random.choice(['shipped', 'delivered'])
            else:
                status = 'delivered'
            
            order = CartOrder.objects.create(
                user=user,
                oid=f"ORD-TEST-{i:04d}",
                price=random.uniform(50, 2000),
                product_status=status,
                order_date=order_date
            )
            orders.append(order)
            
            # Create 2-5 items per order
            for j in range(random.randint(2, 5)):
                price = round(random.uniform(9.99, 399.99), 2)
                qty = random.randint(1, 4)
                
                # Random size based on product type
                size_options = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'One Size', '30x30', '32x32', '34x34', '36x36']
                
                item = CartOrderItems.objects.create(
                    order=order,
                    item=random.choice(product_names),
                    image="https://via.placeholder.com/150",
                    qty=qty,
                    price=price,
                    size=random.choice(size_options),
                    color=random.choice(['Black', 'White', 'Red', 'Blue', 'Green', 'Gray', 'Navy', 'Brown', 'Purple', 'Yellow']),
                    total=price * qty
                )
                order_items.append(item)
        
        return {
            'orders': orders,
            'order_items': order_items
        }

    def create_sample_return(self, order_item, order, user, index, created_date):
        """Create a single sample return request with specified date"""
        
        # Return reasons with weights for realistic distribution
        reasons = [
            ('wrong_size_small', 'Wrong size - too small', 15),
            ('wrong_size_big', 'Wrong size - too big', 15),
            ('defective', 'Defective/Damaged item', 20),
            ('wrong_item', 'Wrong item received', 10),
            ('changed_mind', 'Changed mind / No longer needed', 25),
            ('quality', 'Quality not as expected', 10),
            ('arrived_late', 'Arrived too late', 3),
            ('better_price', 'Found better price elsewhere', 2),
        ]
        
        # Select reason based on weights
        reason_choice = random.choices(
            reasons,
            weights=[r[2] for r in reasons],
            k=1
        )[0]
        
        reason = reason_choice[1]
        reason_code = reason_choice[0]
        
        # Additional details for certain reasons
        reason_details = ''
        if reason_code == 'defective':
            reason_details = random.choice([
                'Button is broken',
                'Zipper is stuck',
                'Stain on fabric',
                'Seam is coming apart',
                'Wrong color received',
                'Product arrived damaged',
                'Missing parts',
                'Does not work',
                'Scratched surface'
            ])
        elif reason_code == 'quality':
            reason_details = random.choice([
                'Material feels cheap',
                'Fits weirdly',
                'Color faded',
                'Poor stitching',
                'Not as described',
                'Too thin',
                'Uncomfortable'
            ])
        elif reason_code == 'arrived_late':
            reason_details = 'Needed it for an event that passed'
        elif reason_code == 'wrong_item':
            reason_details = 'Received different product than ordered'
        
        # Status distribution based on return age
        days_old = (timezone.now() - created_date).days
        
        # Older returns are more likely to be completed/rejected
        if days_old > 365:  # Over 1 year old
            status_weights = {
                'pending': 0,
                'approved': 0,
                'received': 0,
                'completed': 60,
                'rejected': 30,
                'cancelled': 10
            }
        elif days_old > 180:  # 6-12 months old
            status_weights = {
                'pending': 2,
                'approved': 3,
                'received': 5,
                'completed': 55,
                'rejected': 25,
                'cancelled': 10
            }
        elif days_old > 90:  # 3-6 months old
            status_weights = {
                'pending': 5,
                'approved': 8,
                'received': 12,
                'completed': 45,
                'rejected': 20,
                'cancelled': 10
            }
        elif days_old > 30:  # 1-3 months old
            status_weights = {
                'pending': 15,
                'approved': 20,
                'received': 20,
                'completed': 25,
                'rejected': 15,
                'cancelled': 5
            }
        else:  # Less than 30 days old
            status_weights = {
                'pending': 40,
                'approved': 25,
                'received': 15,
                'completed': 10,
                'rejected': 7,
                'cancelled': 3
            }
        
        status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values()),
            k=1
        )[0]
        
        # Return type distribution
        return_type = random.choices(
            ['refund', 'store_credit', 'exchange'],
            weights=[70, 20, 10],
            k=1
        )[0]
        
        # Quantity (usually 1, sometimes more)
        quantity = random.choices(
            [1, 2, 3, 4],
            weights=[75, 15, 7, 3],
            k=1
        )[0]
        
        # Ensure quantity doesn't exceed ordered quantity
        quantity = min(quantity, order_item.qty)
        
        # Calculate refund amount
        refund_amount = order_item.price * quantity
        
        # Calculate timestamps based on created_date
        updated_at = created_date + timedelta(hours=random.randint(1, 72))
        approved_at = None
        completed_at = None
        
        # Add admin fields based on status
        if status in ['approved', 'received', 'completed']:
            # Approval happens within 1-5 days of creation
            approval_delay = random.randint(1, 5)
            approved_at = created_date + timedelta(days=approval_delay)
            updated_at = max(updated_at, approved_at)
            
        if status == 'completed':
            # Completion happens 3-14 days after approval
            completion_delay = random.randint(3, 14)
            completed_at = (approved_at or created_date) + timedelta(days=completion_delay)
            updated_at = max(updated_at, completed_at)
        
        # Create the return request
        return_request = ReturnRequest(
            order_item=order_item,
            order=order,
            user=user,
            return_type=return_type,
            status=status,
            quantity=quantity,
            reason=reason,
            reason_details=reason_details,
            refund_amount=refund_amount,
            created_at=created_date,
            updated_at=updated_at
        )
        
        # Add admin fields based on status
        if status in ['approved', 'received', 'completed']:
            return_request.approved_by = User.objects.filter(is_staff=True).first() or user
            return_request.approved_at = approved_at
            
        if status == 'completed':
            return_request.completed_at = completed_at
            
        if status in ['received', 'completed']:
            # Condition based on reason and age
            if 'defective' in reason.lower():
                item_condition = random.choices(
                    ['used', 'defective'],
                    weights=[30, 70]
                )[0]
            elif 'size' in reason.lower():
                item_condition = random.choices(
                    ['new', 'opened', 'used'],
                    weights=[40, 50, 10]
                )[0]
            elif days_old > 180:
                item_condition = random.choices(
                    ['used', 'defective'],
                    weights=[80, 20]
                )[0]
            else:
                item_condition = random.choices(
                    ['new', 'opened', 'used'],
                    weights=[30, 50, 20]
                )[0]
                
            return_request.item_condition = item_condition
            
            # Add tracking info (less likely for very old returns)
            if days_old < 365 or random.random() > 0.5:
                return_request.tracking_number = f"TRK{random.randint(10000, 99999)}"
                return_request.shipping_carrier = random.choice(['FedEx', 'UPS', 'USPS', 'DHL', 'Canada Post', 'Royal Mail'])
        
        if status == 'rejected':
            return_request.admin_notes = random.choice([
                'Item used beyond return policy',
                'Return window expired',
                'Missing original packaging',
                'Customer changed mind after use',
                'Item shows signs of wear',
                'Return not authorized',
                'Wrong return reason',
                'Item not eligible for return'
            ])
            
        if status == 'cancelled':
            return_request.admin_notes = random.choice([
                'Cancelled by customer',
                'Customer decided to keep item',
                'Duplicate request',
                'Customer initiated new return instead'
            ])
        
        return_request.save()
        
        return return_request

    def show_date_distribution(self):
        """Show distribution of return dates for verification"""
        from django.db.models import Count
        from django.db.models.functions import TruncMonth, TruncYear
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("DATE DISTRIBUTION OF SAMPLE RETURNS (Last 2 Years):")
        self.stdout.write("="*60)
        
        # Group by year
        yearly_counts = ReturnRequest.objects.annotate(
            year=TruncYear('created_at')
        ).values('year').annotate(
            count=Count('id')
        ).order_by('year')
        
        total = ReturnRequest.objects.count()
        
        for item in yearly_counts:
            if item['year']:
                year_str = item['year'].strftime('%Y')
                count = item['count']
                percentage = (count / total * 100) if total > 0 else 0
                bar = '' * int(percentage / 2)
                self.stdout.write(f"{year_str:10} | {bar:30} {count} returns ({percentage:.1f}%)")
        
        self.stdout.write("-"*60)
        
        # Group by month for more detail
        monthly_counts = ReturnRequest.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        self.stdout.write("\nMonthly Breakdown:")
        self.stdout.write("-"*60)
        
        for item in monthly_counts[-12:]:  # Last 12 months
            if item['month']:
                month_str = item['month'].strftime('%b %Y')
                count = item['count']
                percentage = (count / total * 100) if total > 0 else 0
                bar = '' * int(percentage)
                self.stdout.write(f"{month_str:10} | {bar:25} {count} returns ({percentage:.1f}%)")
        
        self.stdout.write("="*60)
        self.stdout.write(f"TOTAL: {total} returns across last 2 years")
        self.stdout.write("="*60)