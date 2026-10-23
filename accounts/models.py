from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    SALES = "sales", "Sales Employee"


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # `createsuperuser` should always produce an Admin-role user.
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Django user + a role used for RBAC."""

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SALES)

    objects = CustomUserManager()

    @property
    def is_admin_role(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_sales_role(self) -> bool:
        return self.role == Role.SALES

    def __str__(self):
        return f"{self.username} ({self.role})"