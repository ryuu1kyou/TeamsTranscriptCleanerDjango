"""
Management command to assign admin roles to existing superusers.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Assign admin role to existing superusers and create test users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create test users with different roles',
        )

    def handle(self, *args, **options):
        """Assign admin roles to superusers."""
        
        # Ensure admin group exists
        admin_group, created = Group.objects.get_or_create(name='admin')
        if created:
            self.stdout.write(
                self.style.SUCCESS("Created admin group")
            )

        # Assign admin role to all superusers
        superusers = User.objects.filter(is_superuser=True)
        assigned_count = 0
        
        for user in superusers:
            if not user.has_role('admin'):
                user.add_role('admin')
                assigned_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Assigned admin role to: {user.email}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"User {user.email} already has admin role")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nAssigned admin role to {assigned_count} superusers")
        )

        # Create test users if requested
        if options['create_test_users']:
            self.create_test_users()

    def create_test_users(self):
        """Create test users with different roles."""
        
        test_users = [
            {
                'email': 'manager@example.com',
                'username': 'manager',
                'first_name': 'Manager',
                'last_name': 'User',
                'roles': ['manager']
            },
            {
                'email': 'editor@example.com', 
                'username': 'editor',
                'first_name': 'Editor',
                'last_name': 'User',
                'roles': ['editor']
            },
            {
                'email': 'viewer@example.com',
                'username': 'viewer', 
                'first_name': 'Viewer',
                'last_name': 'User',
                'roles': ['viewer']
            },
        ]

        created_count = 0
        
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            
            if created:
                user.set_password('testpass123')  # Default password for test users
                user.save()
                created_count += 1
                
                # Assign roles
                for role_name in user_data['roles']:
                    user.add_role(role_name)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created test user: {user.email} with roles: {', '.join(user_data['roles'])}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Test user {user.email} already exists")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nCreated {created_count} test users")
        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.WARNING("\nTest user password: testpass123")
            )