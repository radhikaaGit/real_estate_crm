from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{10,15}$",
    message="Enter a valid phone number: 10 to 15 digits, optional leading '+', no spaces or dashes.",
)


class Lead(models.Model):
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        REFERRAL = "referral", "Referral"
        ADVERTISEMENT = "advertisement", "Advertisement"
        WALK_IN = "walk_in", "Walk-in"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    customer_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=16, validators=[phone_validator])
    email = models.EmailField()
    interested_property = models.CharField(max_length=255)
    budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"), message="Budget must be greater than zero.")],
    )
    lead_source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    lost_reason = models.TextField(blank=True, default="")

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_leads",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_leads",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.customer_name} [{self.status}]"