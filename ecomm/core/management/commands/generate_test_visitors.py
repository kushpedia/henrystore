# your_app/management/commands/generate_test_visitors.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import random
import string
from corporate.models import UniqueVisit  # Replace 'your_app' with your actual app name

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates 50 random visitor records for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to go back for random dates (default: 30)'
        )
        parser.add_argument(
            '--records',
            type=int,
            default=50,
            help='Number of records to generate (default: 50)'
        )

    def handle(self, *args, **options):
        days_back = options['days']
        num_records = options['records']
        
        self.stdout.write(self.style.SUCCESS(f' Generating {num_records} test visitor records...'))
        
        # Clear existing test data (optional - comment out if you want to keep existing data)
        # self.stdout.write('Clearing existing test data...')
        # UniqueVisit.objects.all().delete()
        
        # Get or create test users
        users = self.get_or_create_test_users()
        
        # Generate random IP addresses
        ip_pool = self.generate_ip_pool(20)
        
        # Generate random user agents
        user_agent_pool = self.generate_user_agent_pool(15)
        
        records_created = 0
        today = timezone.now().date()
        
        for i in range(num_records):
            try:
                # Random date within the last X days
                random_days = random.randint(0, days_back)
                visit_date = today - timedelta(days=random_days)
                
                # Randomly decide if this is an authenticated user (30% chance)
                is_authenticated = random.random() < 0.3
                
                if is_authenticated and users:
                    user = random.choice(users)
                else:
                    user = None
                
                # Create the visit record
                visit = UniqueVisit.objects.create(
                    user=user,
                    ip_address=random.choice(ip_pool),
                    user_agent=random.choice(user_agent_pool),
                    visit_date=visit_date
                )
                
                records_created += 1
                
                # Show progress every 10 records
                if records_created % 10 == 0:
                    self.stdout.write(f'   {records_created} records created...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Error creating record: {str(e)}'))
        
        # Generate some additional records with patterns (weekend spikes, etc.)
        self.stdout.write(self.style.SUCCESS('\n Adding pattern-based records for realistic trends...'))
        
        # Add weekend spikes (more visitors on Saturdays and Sundays)
        for week in range(4):  # Last 4 weeks
            for day_offset in [5, 6]:  # Saturday and Sunday
                spike_date = today - timedelta(days=(week * 7) + day_offset)
                if spike_date >= today - timedelta(days=days_back):
                    # Add 3-5 extra records for each weekend day
                    for _ in range(random.randint(3, 5)):
                        UniqueVisit.objects.create(
                            user=random.choice(users) if random.random() < 0.4 else None,
                            ip_address=random.choice(ip_pool),
                            user_agent=random.choice(user_agent_pool),
                            visit_date=spike_date
                        )
                        records_created += 1
        
        # Add some returning visitors (same IP on multiple days)
        self.stdout.write(' Adding returning visitor patterns...')
        returning_ips = random.sample(ip_pool, 5)  # Pick 5 IPs to be returning visitors
        
        for ip in returning_ips:
            # Create visits on 3-5 different days
            visit_days = random.sample(range(days_back), random.randint(3, 5))
            for day in visit_days:
                visit_date = today - timedelta(days=day)
                UniqueVisit.objects.create(
                    user=random.choice(users) if random.random() < 0.6 else None,
                    ip_address=ip,
                    user_agent=random.choice(user_agent_pool),
                    visit_date=visit_date
                )
                records_created += 1
        
        # Final count
        final_count = UniqueVisit.objects.count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(' TEST DATA GENERATION COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f' Records requested: {num_records}')
        self.stdout.write(f' Records created: {records_created}')
        self.stdout.write(f' Total records in database: {final_count}')
        
        # Show sample statistics
        self.stdout.write('\n Sample Statistics:')
        
        # Count by authentication
        auth_count = UniqueVisit.objects.filter(user__isnull=False).count()
        anon_count = UniqueVisit.objects.filter(user__isnull=True).count()
        self.stdout.write(f'    Authenticated visitors: {auth_count}')
        self.stdout.write(f'    Anonymous visitors: {anon_count}')
        
        # Unique IPs
        unique_ips = UniqueVisit.objects.values('ip_address').distinct().count()
        self.stdout.write(f'    Unique IP addresses: {unique_ips}')
        
        # Date range
        if final_count > 0:
            earliest = UniqueVisit.objects.earliest('visit_date').visit_date
            latest = UniqueVisit.objects.latest('visit_date').visit_date
            self.stdout.write(f'   Date range: {earliest} to {latest}')
        
        self.stdout.write(self.style.SUCCESS('\ You can now view your visitor dashboard!'))

    def get_or_create_test_users(self):
        """Create or get test users for authenticated visits"""
        users = []
        try:
            # Try to get existing users first
            users = list(User.objects.filter(is_staff=False)[:10])
            
            # If no users exist, create some test users
            if not users:
                self.stdout.write('   👥 Creating test users...')
                for i in range(1, 6):
                    username = f'testuser{i}'
                    email = f'testuser{i}@example.com'
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'is_active': True
                        }
                    )
                    if created:
                        user.set_password('password123')
                        user.save()
                        self.stdout.write(f'       Created user: {username}')
                    users.append(user)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Could not create test users: {str(e)}'))
        
        return users

    def generate_ip_pool(self, count):
        """Generate a pool of realistic IP addresses"""
        ip_pool = []
        for _ in range(count):
            # Generate realistic IPs (avoid reserved ranges)
            first = random.choice([8, 12, 15, 17, 18, 19, 20, 23, 24, 32, 34, 35, 38, 40, 42, 46, 47, 49, 50, 52, 54, 56, 57, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250])
            ip = f"{first}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
            ip_pool.append(ip)
        return ip_pool

    def generate_user_agent_pool(self, count):
        """Generate a pool of realistic user agents"""
        user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Safari on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Mobile - iPhone
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            
            # Mobile - Android
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Safari on iPad
            "Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            
            # Bots (a few for realism)
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        ]
        
        # If we need more than available, duplicate some
        while len(user_agents) < count:
            user_agents.extend(user_agents[:count-len(user_agents)])
        
        return user_agents[:count]