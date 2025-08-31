"""
Management command to create default roles (groups) for the application.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create default roles and permissions for the application'

    def handle(self, *args, **options):
        """Create default roles."""
        
        # Default roles to create
        default_roles = [
            {
                'name': 'admin',
                'description': 'Administrator with full system access'
            },
            {
                'name': 'manager', 
                'description': 'Manager with user management capabilities'
            },
            {
                'name': 'user_manager',
                'description': 'Can manage user accounts and roles'
            },
            {
                'name': 'editor',
                'description': 'Can edit and manage transcripts'
            },
            {
                'name': 'viewer',
                'description': 'Read-only access to transcripts'
            },
        ]

        created_count = 0
        
        for role_data in default_roles:
            group, created = Group.objects.get_or_create(
                name=role_data['name']
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created role: {role_data['name']}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Role already exists: {role_data['name']}")
                )

        # Assign permissions to roles
        self._assign_permissions()
        
        self.stdout.write(
            self.style.SUCCESS(f"\nCreated {created_count} new roles successfully!")
        )

    def _assign_permissions(self):
        """Assign default permissions to roles."""
        
        try:
            # Get content types
            user_ct = ContentType.objects.get_for_model(User)
            
            # Admin role - all permissions
            admin_group = Group.objects.get(name='admin')
            admin_permissions = Permission.objects.all()
            admin_group.permissions.set(admin_permissions)
            
            # Manager role - user management permissions
            manager_group = Group.objects.get(name='manager')
            manager_permissions = Permission.objects.filter(
                content_type=user_ct
            )
            manager_group.permissions.set(manager_permissions)
            
            # User Manager role - specific user permissions
            user_manager_group = Group.objects.get(name='user_manager')
            user_manager_permissions = Permission.objects.filter(
                content_type=user_ct,
                codename__in=['view_user', 'change_user', 'add_user']
            )
            user_manager_group.permissions.set(user_manager_permissions)
            
            self.stdout.write(
                self.style.SUCCESS("Assigned default permissions to roles")
            )
            
        except Group.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f"Error assigning permissions: {e}")
            )