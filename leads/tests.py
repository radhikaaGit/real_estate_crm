from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User

from .models import Lead


class LeadAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="Admin@123", role=Role.ADMIN)
        self.s1 = User.objects.create_user("s1", password="Sales@123", role=Role.SALES)
        self.s2 = User.objects.create_user("s2", password="Sales@123", role=Role.SALES)
        self.lead1 = self.make_lead("Lead One", self.s1)
        self.lead2 = self.make_lead("Lead Two", self.s2)
        self.list_url = reverse("lead-list")

    def make_lead(self, name, employee, **kw):
        data = dict(
            customer_name=name, phone_number="9876543210", email="a@b.com",
            interested_property="2BHK", budget="1000000", lead_source="website",
            assigned_to=employee,
        )
        data.update(kw)
        return Lead.objects.create(**data)

    def login(self, username, password):
        resp = self.client.post(reverse("login"), {"username": username, "password": password})
        self.assertEqual(resp.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        return resp

    def payload(self, **kw):
        data = {
            "customer_name": "New Customer", "phone_number": "9999999999",
            "email": "new@example.com", "interested_property": "3BHK",
            "budget": "5000000", "lead_source": "referral",
        }
        data.update(kw)
        return data

    # ------------------------------------------------------------ auth
    def test_login_and_refresh(self):
        resp = self.login("admin", "Admin@123")
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["role"], "admin")
        self.client.credentials()
        r = self.client.post(reverse("token-refresh"), {"refresh": resp.data["refresh"]})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_wrong_credentials(self):
        r = self.client.post(reverse("login"), {"username": "admin", "password": "bad"})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_is_401(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 401)

    # ------------------------------------------------------------ RBAC
    def test_admin_sees_all_employee_sees_own(self):
        self.login("admin", "Admin@123")
        self.assertEqual(self.client.get(self.list_url).data["count"], 2)
        self.login("s1", "Sales@123")
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["id"], self.lead1.id)

    def test_employee_cannot_access_other_lead(self):
        self.login("s1", "Sales@123")
        url = reverse("lead-detail", args=[self.lead2.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"status": "won"}).status_code, 404)

    def test_employee_cannot_create_or_delete(self):
        self.login("s1", "Sales@123")
        self.assertEqual(self.client.post(self.list_url, self.payload()).status_code, 403)
        url = reverse("lead-detail", args=[self.lead1.id])
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_admin_crud(self):
        self.login("admin", "Admin@123")
        r = self.client.post(self.list_url, self.payload(assigned_to=self.s1.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["created_by"], self.admin.id)
        url = reverse("lead-detail", args=[r.data["id"]])
        self.assertEqual(self.client.patch(url, {"status": "contacted"}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    # ------------------------------------------------------------ assign
    def test_only_admin_can_assign(self):
        url = reverse("lead-assign", args=[self.lead1.id])
        self.login("s1", "Sales@123")
        self.assertEqual(self.client.post(url, {"assigned_to": self.s2.id}).status_code, 403)
        self.login("admin", "Admin@123")
        r = self.client.post(url, {"assigned_to": self.s2.id})
        self.assertEqual(r.status_code, 200)
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.assigned_to_id, self.s2.id)

    def test_cannot_assign_to_admin_or_missing_user(self):
        self.login("admin", "Admin@123")
        url = reverse("lead-assign", args=[self.lead1.id])
        self.assertEqual(self.client.post(url, {"assigned_to": self.admin.id}).status_code, 400)
        self.assertEqual(self.client.post(url, {"assigned_to": 9999}).status_code, 400)
        self.assertEqual(self.client.post(url, {}).status_code, 400)

    def test_employee_cannot_change_assigned_to_via_patch(self):
        self.login("s1", "Sales@123")
        url = reverse("lead-detail", args=[self.lead1.id])
        r = self.client.patch(url, {"assigned_to": self.s2.id})
        self.assertEqual(r.status_code, 403)
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.assigned_to_id, self.s1.id)

    def test_employee_can_update_status_and_details(self):
        self.login("s1", "Sales@123")
        url = reverse("lead-detail", args=[self.lead1.id])
        r = self.client.patch(url, {"status": "qualified", "budget": "2000000"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "qualified")

    # ------------------------------------------------------------ validation
    def test_lost_requires_reason(self):
        self.login("s1", "Sales@123")
        url = reverse("lead-detail", args=[self.lead1.id])
        r = self.client.patch(url, {"status": "lost"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("lost_reason", r.data)
        r = self.client.patch(url, {"status": "lost", "lost_reason": "Budget too low"})
        self.assertEqual(r.status_code, 200)

    def test_field_validation(self):
        self.login("admin", "Admin@123")
        bad = self.client.post(self.list_url, self.payload(
            email="not-an-email", phone_number="abc", budget="-5"))
        self.assertEqual(bad.status_code, 400)
        for f in ("email", "phone_number", "budget"):
            self.assertIn(f, bad.data)
        self.assertEqual(self.client.post(self.list_url, self.payload(budget="0")).status_code, 400)
        missing = self.client.post(self.list_url, {})
        self.assertEqual(missing.status_code, 400)
        self.assertIn("customer_name", missing.data)

    # ------------------------------------------------------------ list features
    def test_filter_search_pagination(self):
        self.make_lead("Searchable Sam", self.s1, status="won", lead_source="walk_in")
        self.login("admin", "Admin@123")
        self.assertEqual(self.client.get(self.list_url, {"status": "won"}).data["count"], 1)
        self.assertEqual(self.client.get(self.list_url, {"lead_source": "walk_in"}).data["count"], 1)
        self.assertEqual(self.client.get(self.list_url, {"search": "Searchable"}).data["count"], 1)
        self.assertEqual(self.client.get(self.list_url, {"status": "bogus"}).status_code, 400)

        # pagination: PAGE_SIZE = 10 -> create 9 more (total 12) => page 1 has 10, page 2 has 2
        for i in range(9):
            self.make_lead(f"Bulk {i}", self.s1)
        r = self.client.get(self.list_url)
        self.assertEqual(r.data["count"], 12)
        self.assertEqual(len(r.data["results"]), 10)
        self.assertIsNotNone(r.data["next"])
        r2 = self.client.get(self.list_url, {"page": 2})
        self.assertEqual(len(r2.data["results"]), 2)

    def test_employees_endpoint_admin_only(self):
        self.login("s1", "Sales@123")
        self.assertEqual(self.client.get(reverse("employees")).status_code, 403)
        self.login("admin", "Admin@123")
        self.assertEqual(self.client.get(reverse("employees")).data["count"], 2)