# FreelanceHub — Project Brief for Claude

## Project Overview

**FreelanceHub** is a multi-tenant SaaS web portal for independent freelancers (barbers, plumbers, electricians, tutors, cleaners, photographers, etc.) to manage their business end-to-end: bookings, customers, invoicing, and payments — all in one place.

---

## Tech Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Frontend     | React + TypeScript + Tailwind CSS + Vite        |
| Backend      | FastAPI (Python 3.12+)                          |
| Database     | PostgreSQL 16 (via SQLAlchemy + Alembic)        |
| Auth         | JWT (access + refresh tokens) + bcrypt          |
| Email        | SMTP / SendGrid for notifications               |
| File Storage | Local filesystem (dev) / S3-compatible (prod)   |
| API Docs     | FastAPI auto-generated OpenAPI / Swagger UI     |
| Deployment   | Docker + Docker Compose                         |

### Additional Libraries (Frontend)
- `react-router-dom` — routing
- `react-query` (TanStack Query) — server state & caching
- `react-hook-form` + `zod` — forms & validation
- `date-fns` — date/time utilities
- `recharts` — analytics charts
- `@headlessui/react` — accessible UI primitives
- `lucide-react` — icons

### Additional Libraries (Backend)
- `pydantic v2` — data validation & settings
- `sqlalchemy` (async) + `asyncpg` — ORM & DB driver
- `alembic` — database migrations
- `python-jose` — JWT handling
- `passlib` — password hashing
- `celery` + `redis` — background task queue (reminders, emails)
- `reportlab` or `weasyprint` — PDF invoice generation
- `pytest` + `httpx` — testing

---

## Core Features

### 1. Authentication & Multi-Tenancy
- Freelancer registration & login (email + password)
- JWT-based auth with refresh token rotation
- Each freelancer is an isolated tenant (data scoped by `freelancer_id`)
- Optional: OAuth login (Google)
- Password reset via email OTP

### 2. Freelancer Profile & Business Setup
- Profile: name, bio, avatar, business name, contact info
- **Service Category** selection: Barber, Plumber, Electrician, Tutor, Cleaner, Photographer, Personal Trainer, etc. (extensible enum + custom category)
- Services catalogue: define services with name, duration (minutes), price
- Working hours configuration: per-day schedule (open/close times, breaks)
- Holiday / blocked-date management
- Public booking page URL: `freelancehub.app/{username}`

### 3. Booking System (Customer-Facing)
- Public booking page (no login required for customers)
- Dynamic service selection → date picker (shows available slots based on working hours & existing bookings) → customer details form → confirmation
- Real-time slot availability calculation
- Booking confirmation email (to both customer and freelancer)
- Automated reminder emails (24h and 2h before appointment) via Celery
- Customer can cancel/reschedule via unique link in email
- Support for buffer time between appointments

### 4. Booking Management (Freelancer Dashboard)
- Calendar view (day / week / month)
- List view with filters: status (pending, confirmed, completed, cancelled, no-show), date range, service type
- Create manual bookings
- Update booking status
- Add notes to bookings
- Bulk actions (confirm, cancel)

### 5. Customer Database (CRM Lite)
- Customer profiles: name, email, phone, address, notes, tags
- Auto-created on first booking; editable by freelancer
- Full booking history per customer
- Customer search & filter
- Add/edit/delete customers manually
- Export customer list to CSV

### 6. Invoicing & Billing
- Auto-generate invoice from completed booking
- Manual invoice creation (for ad-hoc work)
- Invoice line items: service, quantity, unit price, discount, tax (configurable rate)
- Invoice statuses: draft, sent, paid, overdue, void
- PDF invoice generation and download
- Send invoice by email directly from dashboard
- Mark invoice as paid (manual) or integrate payment link
- Invoice number auto-sequencing per freelancer (e.g. INV-0001)

### 7. Finance Dashboard
- Revenue summary: today / this week / this month / custom range
- Revenue by service breakdown (bar/pie chart)
- Outstanding invoices total
- Upcoming bookings value
- Recent transactions list
- Monthly revenue trend (line chart)
- Export financial report to CSV/PDF

### 8. Notifications & Reminders
- In-app notification bell (new bookings, cancellations, invoice paid)
- Email notifications: booking confirmation, reminder, cancellation, invoice sent/paid
- Freelancer can configure which notifications to receive

### 9. Settings
- Business info & branding (logo, business name, accent color for public page)
- Services management (CRUD)
- Working hours & availability
- Tax settings (GST/VAT rate, tax number)
- Invoice customisation (logo, footer note, payment terms)
- Notification preferences
- Account security (change password, active sessions)
- Danger zone: delete account

---

## Additional Features Identified

### Must-Have (v1)
- **Waitlist management** — when a slot is cancelled, notify waitlisted customers
- **Recurring bookings** — allow setting up weekly/fortnightly repeat bookings
- **Staff / Team mode** — freelancer can add team members (e.g. a barbershop with 3 barbers), each with their own schedule
- **Custom booking form fields** — freelancer can add extra questions to the booking form (e.g. "What style do you want?")
- **Stripe / PayPal payment integration** — collect payment at time of booking or invoice
- **Public reviews** — customers can leave a star rating + comment after completed booking

### Nice-to-Have (v2)
- **SMS reminders** via Twilio (in addition to email)
- **Mobile-responsive PWA** with offline capability
- **Analytics & reporting** — customer retention, peak hours heatmap
- **Subscription/packages** — sell bundles of sessions (e.g. 10 haircuts)
- **Promo codes & discounts**
- **Multi-language support** (i18n)
- **White-label** — freelancer uses their own domain (CNAME)
- **Google Calendar / Outlook sync**
- **Zapier webhook integration**

---

## Database Schema (Key Tables)

```
freelancers          — tenant accounts
service_categories   — barber, plumber, etc. (seed data + custom)
services             — per-freelancer service catalogue
working_hours        — per-freelancer weekly schedule
blocked_dates        — holidays, one-off unavailability
customers            — per-freelancer CRM records
bookings             — appointments (links freelancer, customer, service)
invoices             — billing records
invoice_line_items   — line items per invoice
payments             — payment records against invoices
notifications        — in-app notification log
```

---

## Project Structure

```
freelancehub/
├── frontend/                    # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── api/                 # Axios/fetch API client, typed endpoints
│   │   ├── components/          # Shared UI components
│   │   │   ├── ui/              # Base: Button, Input, Modal, Badge, etc.
│   │   │   ├── layout/          # Sidebar, Navbar, PageWrapper
│   │   │   └── features/        # Feature-specific components
│   │   ├── pages/               # Route-level page components
│   │   │   ├── auth/            # Login, Register, ForgotPassword
│   │   │   ├── dashboard/       # Home dashboard
│   │   │   ├── bookings/        # Calendar + list views
│   │   │   ├── customers/       # CRM pages
│   │   │   ├── invoices/        # Invoice list + detail
│   │   │   ├── finance/         # Finance dashboard
│   │   │   ├── settings/        # All settings pages
│   │   │   └── public/          # Public booking page (no auth)
│   │   ├── hooks/               # Custom React hooks
│   │   ├── store/               # Zustand global state (auth, UI)
│   │   ├── types/               # TypeScript interfaces & enums
│   │   ├── utils/               # Helpers (date, currency, validation)
│   │   └── constants/           # App-wide constants
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── freelancers.py
│   │   │   │   ├── services.py
│   │   │   │   ├── bookings.py
│   │   │   │   ├── customers.py
│   │   │   │   ├── invoices.py
│   │   │   │   ├── payments.py
│   │   │   │   ├── finance.py
│   │   │   │   └── public.py      # No-auth booking endpoints
│   │   │   └── deps.py            # Dependency injection (get_db, get_current_user)
│   │   ├── core/
│   │   │   ├── config.py          # Settings via pydantic-settings
│   │   │   ├── security.py        # JWT, password hashing
│   │   │   └── celery_app.py      # Celery worker config
│   │   ├── db/
│   │   │   ├── base.py            # SQLAlchemy declarative base
│   │   │   ├── session.py         # Async session factory
│   │   │   └── models/            # SQLAlchemy ORM models (one file per table)
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── crud/                  # CRUD operations (one file per model)
│   │   ├── services/              # Business logic layer
│   │   │   ├── booking_service.py # Slot availability, conflict detection
│   │   │   ├── invoice_service.py # Invoice generation, PDF
│   │   │   └── email_service.py   # Email sending
│   │   ├── tasks/                 # Celery tasks (reminders, emails)
│   │   └── main.py                # FastAPI app factory
│   ├── alembic/                   # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── CLAUDE.md                      # ← this file
```

---

## API Design Conventions

- **Base URL**: `/api/v1/`
- **Auth**: Bearer token in `Authorization` header
- **Response envelope**:
  ```json
  { "data": {}, "message": "ok", "pagination": {} }
  ```
- **Error format**:
  ```json
  { "detail": "Human readable error", "code": "SNAKE_CASE_ERROR_CODE" }
  ```
- **Pagination**: `?page=1&page_size=20` → `{ items, total, page, pages }`
- **Dates**: ISO 8601 strings (`2025-03-09T14:00:00Z`) throughout
- **Currency**: Store as integers (cents/pence) in DB; format in frontend

---

## Key Business Logic Rules

1. **Slot availability**: A slot is available if it falls within working hours AND does not overlap with an existing confirmed/pending booking (accounting for service duration + buffer time).
2. **Multi-tenancy**: Every DB query MUST filter by `freelancer_id`. No cross-tenant data leakage.
3. **Invoice numbering**: Sequential per freelancer, never reuse numbers. Format: `INV-{year}-{sequence}`.
4. **Booking cancellation window**: Configurable per freelancer (e.g. no cancellations within 2 hours).
5. **Timezone**: Store all datetimes in UTC; convert to freelancer's configured timezone for display.

---

## Environment Variables (`.env.example`)

```env
# App
APP_ENV=development
SECRET_KEY=change-me-in-production
ALLOWED_ORIGINS=http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/freelancehub

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAIL_FROM=noreply@freelancehub.app

# Storage
STORAGE_BACKEND=local   # or s3
S3_BUCKET=
S3_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Stripe (optional)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# App URL (for public booking links)
APP_BASE_URL=http://localhost:5173
```

---

## Development Setup

```bash
# 1. Clone repo
git clone <repo>
cd freelancehub

# 2. Start infrastructure
docker compose up -d postgres redis

# 3. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Frontend
cd frontend
npm install
npm run dev   # → http://localhost:5173

# 5. Celery worker (optional for email/reminders)
celery -A app.core.celery_app worker --loglevel=info
```

---

## Coding Standards

### TypeScript / Frontend
- Strict TypeScript (`strict: true` in tsconfig)
- All API response types defined in `src/types/`
- No `any` — use `unknown` + type guards if needed
- Component files: PascalCase (`BookingCard.tsx`)
- Hook files: camelCase prefixed with `use` (`useBookings.ts`)
- Always handle loading, error, and empty states in UI
- Use `react-query` for all server data — no manual `useEffect` fetching

### Python / Backend
- Python 3.12+, type hints everywhere
- Async all the way — use `async def` for all route handlers and DB calls
- `pydantic v2` for all input/output validation
- Separate schemas from models (never return ORM objects directly)
- Business logic lives in `services/`, not in route handlers
- All endpoints require auth except `/api/v1/public/*`
- Write tests for all service layer functions

---

## Security Checklist

- [ ] Passwords hashed with bcrypt (min cost 12)
- [ ] JWT access token TTL: 15 minutes; refresh token TTL: 7 days
- [ ] Refresh token rotation on every use
- [ ] All authenticated endpoints validate `freelancer_id` ownership
- [ ] Rate limiting on auth endpoints (fastapi-limiter)
- [ ] CORS restricted to known origins
- [ ] SQL injection impossible via SQLAlchemy ORM (no raw strings)
- [ ] File upload: validate MIME type + size limit (5 MB)
- [ ] Invoice PDF download gated — only owner can download
- [ ] Public booking page rate-limited

---

## Testing Strategy

- **Unit tests**: service layer functions (booking logic, invoice calc)
- **Integration tests**: API endpoints with a test DB (pytest + httpx async client)
- **Frontend**: component tests with Vitest + React Testing Library
- Target: 80%+ coverage on backend services

---

## Deployment (Production)

- Containerised with Docker
- Nginx reverse proxy in front of FastAPI + static frontend build
- PostgreSQL with daily backups
- Redis for Celery broker + result backend
- Environment secrets via `.env` or secrets manager
- HTTPS via Let's Encrypt (certbot)

---

## Phase Roadmap

| Phase | Scope                                                                 |
|-------|-----------------------------------------------------------------------|
| 1     | Auth, profile setup, services, working hours, public booking page     |
| 2     | Booking management (dashboard, calendar), customer DB                 |
| 3     | Invoicing, PDF generation, email delivery                             |
| 4     | Finance dashboard, charts                                             |
| 5     | Notifications, reminders (Celery), cancellation/reschedule flows      |
| 6     | Stripe payments, reviews, recurring bookings                          |
| 7     | Team/staff mode, SMS, mobile PWA, Google Calendar sync                |
