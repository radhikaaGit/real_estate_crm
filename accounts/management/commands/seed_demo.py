from django.core.management.base import BaseCommand

from accounts.models import Role, User
from leads.models import Lead


class Command(BaseCommand):
    help = "Creates demo users (1 admin, 2 sales) and a few sample leads."

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "role": Role.ADMIN,
                      "is_staff": True, "is_superuser": True},
        )
        admin.set_password("Admin@123")
        admin.save()

        sales = []
        for name in ("sales1", "sales2"):
            u, _ = User.objects.get_or_create(
                username=name,
                defaults={"email": f"{name}@example.com", "role": Role.SALES},
            )
            u.set_password("Sales@123")
            u.save()
            sales.append(u)

        if not Lead.objects.exists():
            samples = [
                ("Rahul Sharma", "9876543210", "rahul@example.com", "2BHK Vijay Nagar", "4500000", "website", sales[0]),
                ("Priya Verma", "9123456780", "priya@example.com", "3BHK Palasia", "7500000", "referral", sales[0]),
                ("Amit Jain", "9988776655", "amit@example.com", "Plot Bypass Road", "2500000", "walk_in", sales[1]),
                ("Neha Singh", "9001122334", "neha@example.com", "1BHK Rau", "2000000", "advertisement", None),
            ]
            for n, p, e, prop, b, src, emp in samples:
                Lead.objects.create(
                    customer_name=n, phone_number=p, email=e,
                    interested_property=prop, budget=b, lead_source=src,
                    assigned_to=emp, created_by=admin,
                )

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready.\n"
            "  admin  / Admin@123  (Admin)\n"
            "  sales1 / Sales@123  (Sales Employee)\n"
            "  sales2 / Sales@123  (Sales Employee)"
        ))