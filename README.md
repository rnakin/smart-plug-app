# KnowWatt — Smart Home Energy Management System

Django + PostgreSQL backend with JWT auth, multi-household support, NFC device identification, and energy monitoring.

---

## Project Progress

| Phase | Status | Progress |
|-------|--------|----------|
| **Phase 1: Django + PostgreSQL Setup** | ✅ Complete | 100% |
| **Phase 2: Auth Service** | ✅ Complete | 100% |
| **Phase 3: User & House Service** | ✅ Complete | 100% |
| **Phase 4: Device Service** | ✅ Complete | 100% |
| **Phase 5: Energy Service** | ✅ Complete | 100% |
| Phase 6: Alert Service | ⏳ Pending | 0% |

---

## Running the App

```bash
# Copy env file
cp .env_example .env

# Start with Docker Compose
docker compose up --build

# Apply migrations (first time)
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

App runs at `http://localhost:8000`

---

## API Overview

All API endpoints require JWT authentication unless noted.

### Auth (`/auth/`)

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/auth/register/` | Register with email + password |
| POST | `/auth/login/` | Login → returns access + refresh tokens |
| POST | `/auth/logout/` | Logout (blacklist refresh token) |
| POST | `/auth/token/refresh/` | Refresh access token |
| POST | `/auth/verify-email/` | Verify email with token |
| POST | `/auth/forgot-password/` | Send password reset email |
| POST | `/auth/reset-password/` | Reset password with token |
| GET  | `/auth/me/` | Get current user info |

### Houses (`/api/houses/`)

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/houses/` | List user's houses |
| POST | `/api/houses/` | Create house (creator = owner) |
| GET | `/api/houses/<id>/` | House details |
| PATCH | `/api/houses/<id>/` | Update house (owner only) |
| DELETE | `/api/houses/<id>/` | Delete house (owner only) |
| GET | `/api/houses/<id>/users/` | List members |
| POST | `/api/houses/<id>/users/invite/` | Invite member by email |
| POST | `/api/houses/<id>/users/manage/` | Remove / update role |

### Smart Plugs

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/houses/<id>/plugs/` | List plugs |
| POST | `/api/houses/<id>/plugs/` | Register plug (QR/manual code) |
| GET/PATCH/DELETE | `/api/houses/<id>/plugs/<plug_id>/` | Plug detail |
| POST | `/api/houses/<id>/plugs/<plug_id>/control/` | Remote on/off |

### Electrical Devices

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/houses/<id>/devices/` | List devices |
| POST | `/api/houses/<id>/devices/` | Create device |
| GET/PATCH/DELETE | `/api/houses/<id>/devices/<device_id>/` | Device detail |

### NFC Tags

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/houses/<id>/nfc/` | List NFC tags |
| POST | `/api/houses/<id>/nfc/register/` | Register NFC tag |
| GET/PATCH/DELETE | `/api/houses/<id>/nfc/<tag_id>/` | Tag detail |
| POST | `/api/nfc/scan/` | NFC tap event (returns device or unknown signal) |

### Energy (`/api/houses/<id>/energy/`)

| Method | URL | Description |
|--------|-----|-------------|
| POST | `.../energy/ingest/` | Ingest reading from plug firmware |
| GET | `.../energy/realtime/` | Latest reading per plug |
| GET | `.../energy/dashboard/` | Combined dashboard (today/week/month kWh, top devices) |
| GET | `.../energy/summary/?period=daily\|weekly\|monthly` | Aggregated summary |
| GET | `.../energy/by-device/` | Energy breakdown per device |
| GET | `.../energy/by-plug/` | Energy breakdown per plug |
| GET | `.../energy/readings/` | Raw readings (paginated) |
| GET | `.../energy/export/?format=csv\|json` | Export readings as CSV or JSON |

**Common query params:** `start=YYYY-MM-DD`, `end=YYYY-MM-DD`, `plug_id`, `device_id`

---

## Role Permissions

| Role | Permissions |
|------|-------------|
| **Owner** | Full access, manage members, delete house |
| **Admin** | Manage devices/plugs, manage members (except owner) |
| **Member** | View & control devices, view members |
| **Guest** | View only (read-only) |

---

## Data Models

```
House
  └── HouseMember (owner/admin/member/guest)
  └── SmartPlug (plug_code, name, location, is_on, online_status)
       └── PlugSession (active device session via NFC)
       └── EnergyReading (voltage, current, power, energy_kwh, recorded_at)
  └── ElectricalDevice (name, type, rated_power_w, risk_level, auto_cutoff_minutes)
       └── NFCTag (tag_uid, label) — one device → many tags
  └── DailyEnergySummary (pre-aggregated per plug per day)
```

---

## Tech Stack

- **Backend:** Django 5, Django REST Framework, SimpleJWT
- **Database:** PostgreSQL
- **Auth:** JWT (access + refresh tokens), email verification
- **Containerization:** Docker + Docker Compose
