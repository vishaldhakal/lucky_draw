from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

class Organization(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    logo = models.FileField(upload_to='organizations/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')
        
        # Remove organization requirement for superuser
        extra_fields.setdefault('organization', None)
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_ROLES = (
        ('Admin', 'Admin'),
        ('Organization Head', 'Organization Head'),
        ('Manager', 'Manager'),
        ('Other', 'Other'),
    )
    
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=100, choices=USER_ROLES, default='Organization Head')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Remove 'organization' from here

    def __str__(self):
        org_name = self.organization.name if self.organization else "No Organization"
        return f"{self.email} ({self.get_role_display()} at {org_name})"

    def clean(self):
        if self.role == 'Admin' and self.organization and CustomUser.objects.filter(organization=self.organization, role='Admin').exclude(pk=self.pk).exists():
            raise ValidationError('An organization can have only one admin.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def create_org_admin(cls, email, password, organization_name):
        org = Organization.objects.create(name=organization_name)
        return cls.objects.create_user(email=email, password=password, organization=org, role='Admin')

    def add_user_to_org(self, email, password, role='Agent'):
        if self.role != 'Admin':
            raise ValidationError('Only admins can add users to the organization.')
        if not self.organization:
            raise ValidationError('Admin is not associated with any organization.')
        return CustomUser.objects.create_user(email=email, password=password, organization=self.organization, role=role)

    class Meta:
        permissions = [
            ("can_manage_users", "Can manage users"),
            ("can_manage_organization", "Can manage organization"),
        ]