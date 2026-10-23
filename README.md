# Real Estate CRM - Lead Management API

Django REST Framework project with JWT authentication (SimpleJWT), role based access control
(Admin / Sales Employee), object level permissions, validation, search, filtering and pagination.

## Setup

```bash
# 1. virtual environment (inside the real_estate_crm folder)
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Mac / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. create database tables (migrations are already included)
python manage.py migrate

# 4. demo users + sample leads (needed for the Postman collection)
python manage.py seed_demo

# 5. run the server
python manage.py runserver
```

Base URL: `http://127.0.0.1:8000`

Demo credentials created by `seed_demo`:

| Username | Password  | Role           |
|----------|-----------|----------------|
| admin    | Admin@123 | Admin          |
| sales1   | Sales@123 | Sales Employee |
| sales2   | Sales@123 | Sales Employee |

Extra users: `python manage.py createsuperuser` (gets the Admin role automatically) or via the
Django admin panel `/admin/` (set the **Role** field).

Run the automated tests: `python manage.py test`

## Endpoints

| Method | URL | Access | Description |
|--------|-----|--------|-------------|
| POST | `/api/auth/login/` | Public | Returns `access`, `refresh`, `user` |
| POST | `/api/auth/refresh/` | Public | Returns a new `access` token |
| GET | `/api/auth/me/` | Authenticated | Current user |
| GET | `/api/auth/employees/` | Admin | Sales employees list (to pick an assignee) |
| GET | `/api/leads/` | Admin: all, Employee: own | List with search / filter / pagination |
| POST | `/api/leads/` | Admin | Create lead |
| GET | `/api/leads/{id}/` | Admin / assigned employee | Retrieve |
| PUT, PATCH | `/api/leads/{id}/` | Admin / assigned employee | Update details and status |
| DELETE | `/api/leads/{id}/` | Admin | Delete |
| POST | `/api/leads/{id}/assign/` | Admin | Body: `{"assigned_to": <employee_id>}` |

Send the token as header `Authorization: Bearer <access_token>`.
(The access token is valid for 5 minutes, use `/api/auth/refresh/` or log in again.)

### Query parameters for `GET /api/leads/`

- `status` = new | contacted | qualified | won | lost
- `lead_source` = website | referral | advertisement | walk_in
- `search` = customer name, email, phone or interested property
- `ordering` = `created_at`, `-created_at`, `budget`, `customer_name`, `status`
- `page` (10 leads per page)

Example: `/api/leads/?status=new&lead_source=website&search=rahul&page=1`

### Sample create body (Admin)

```json
{
  "customer_name": "Rahul Sharma",
  "phone_number": "9876543210",
  "email": "rahul@example.com",
  "interested_property": "2BHK Vijay Nagar",
  "budget": "4500000",
  "lead_source": "website",
  "assigned_to": 2
}
```

## Business rules and where they are implemented

| Rule | Implementation |
|------|----------------|
| All lead APIs protected | `IsAuthenticated` + `JWTAuthentication` as defaults in `settings.py` |
| Employee sees only own leads | `LeadViewSet.get_queryset()` filters `assigned_to=request.user` (other leads give 404, so their existence is not leaked) |
| Object level permission | `leads/permissions.py` -> `IsAdminOrAssignedEmployee` |
| Only Admin can create / delete / assign | `LeadViewSet.get_permissions()` with `accounts/permissions.py` -> `IsAdminRole` |
| Employee cannot assign / tamper protected fields | `LeadEmployeeSerializer`: `assigned_to`, `created_by`, `created_at`, `updated_at`, `id` are read-only; trying to change `assigned_to` / `created_by` returns 403 |
| Lost lead needs a reason | `LeadBaseSerializer.validate()` -> 400 with `lost_reason` error |
| Field validation | required fields, email, phone (`^\+?[0-9]{10,15}$`), budget > 0, valid choices |
| Assignee must be a sales employee | `assigned_to` only accepts active users with role `sales` |

## Status codes

`200` OK, `201` Created, `204` Deleted, `400` Validation error, `401` Missing / invalid / expired token,
`403` Logged in but not allowed, `404` Lead not found or not accessible.

Validation error example:

```json
{ "email": ["Enter a valid email address."], "budget": ["Budget must be greater than zero."] }
```

## Postman

1. Import `postman/RealEstateCRM.postman_collection.json`.
2. Start the server and make sure `python manage.py seed_demo` was run.
3. Open the collection -> **Run** (Collection Runner) -> run all. Folders run in order and tokens / ids are
   stored automatically. Every request has test assertions. Change the `base_url` variable if needed.

Folders: Authentication, Admin - Leads, Sales Employee - RBAC, Validation Errors, Unauthorized, Cleanup.

## Project structure

```
real_estate_crm/
├── manage.py
├── requirements.txt
├── README.md
├── config/        settings.py, urls.py, wsgi.py, asgi.py
├── accounts/      User model (role), login, me, employees, IsAdminRole, seed_demo command
├── leads/         Lead model, serializers, permissions, filters, views, urls, tests
└── postman/       RealEstateCRM.postman_collection.json
```

**Requires Python 3.12 or newer.**
