# Capture Moments – Photographer Booking System

A Django web app where **clients** find photographers, view portfolios, check availability and send booking
requests, and **photographers** accept or reject them. An **admin** manages everything.

> **Status honesty note**
> The code was written and statically checked (Python syntax, template tag balance, URL names).
> It was written in an environment **without Django installed**, so the server and the automated tests
> have **not been run by the author**. Follow Part 3 below to run the tests and the manual checklist on your
> own computer. Treat a feature as working only after it passes there.
> The AWS part (Part 6) is written but **untested** – nobody has deployed it yet.

---------------------------------------------------------------------

## Part 1 – Project plan

| Phase | What you do | Result |
|------|-------------|--------|
| 1 | Install Python, create virtual environment, install Django | Tools ready |
| 2 | Create database tables (models + migrations) | Users, photographers, bookings stored in SQLite |
| 3 | Registration, login, logout, role-based dashboards | Client / Photographer / Admin can sign in |
| 4 | Photographer profile, portfolio upload, search & filter | Clients can find photographers |
| 5 | Availability calendar + booking form + validation | Clients can request a date |
| 6 | Accept/reject, client history, notifications | Full booking life-cycle |
| 7 | Admin dashboard | Manage clients, photographers, bookings |
| 8 | Run tests, fix problems | Confidence it works |
| 9 | AWS: S3 for images, IAM role, EC2 hosting | Live website (see `docs/AWS_GUIDE.md`) |

### Which feature lives where

| # | Requirement | Where it is implemented |
|---|-------------|-------------------------|
| 1 | Photography-themed home page | `templates/core/home.html`, `static/css/style.css` |
| 2 | Client register/login | `accounts/` |
| 3 | Photographer register/login | `accounts/` (same login, different register form) |
| 4 | Profiles (photo, services, experience, location, price) | `photographers/models.py` → `PhotographerProfile` |
| 5 | Portfolio gallery | `PortfolioImage` model, upload page, lightbox on detail page |
| 6 | Search & filter (category, location, price) | `photographers/views.py` → `photographer_list` |
| 7 | Availability calendar | `bookings/availability.py` (+ `BlockedDate` model) |
| 8 | Booking request form | `bookings/forms.py`, `bookings/views.py` → `create_booking` |
| 9 | Photographer dashboard (accept/reject) | `bookings/views.py` → `photographer_dashboard`, `respond_booking` |
| 10 | Client dashboard (status + history) | `bookings/views.py` → `client_dashboard` |
| 11 | Notifications | `Notification` model, `bookings/notifications.py`, bell icon in navbar (+ console email) |
| 12 | Admin dashboard | `/admin-dashboard/` (custom) and `/django-admin/` (built-in) |

### Folder structure

```
capture_moments/
├── manage.py                  # command-line tool: runserver, migrate, test...
├── requirements.txt           # Python packages for local development
├── requirements-aws.txt       # extra packages for AWS (S3, gunicorn)
├── .env.example               # settings you will use on AWS
├── config/                    # project settings
│   ├── settings.py            # ALL configuration (database, S3 switch, email...)
│   ├── urls.py                # top-level URL routing
│   └── wsgi.py
├── accounts/                  # users, registration, login
│   ├── models.py              # custom User (role: client / photographer)
│   ├── forms.py  views.py  urls.py  admin.py
├── photographers/             # profiles, portfolio, search, availability
│   ├── models.py              # Category, PhotographerProfile, PortfolioImage, BlockedDate
│   ├── forms.py  views.py  urls.py  admin.py  validators.py
├── bookings/                  # booking life-cycle + notifications
│   ├── models.py              # Booking, Notification
│   ├── availability.py        # "is the photographer free?" + calendar builder
│   ├── forms.py  views.py  urls.py  admin.py  notifications.py  context_processors.py
├── core/                      # home page, admin dashboard, helpers
│   ├── views.py  urls.py  forms.py  decorators.py  tests.py
│   └── management/commands/seed_data.py   # creates categories + demo data
├── templates/                 # HTML pages (Bootstrap 5)
│   ├── base.html  partials/  core/  accounts/  photographers/  bookings/
├── static/                    # css/style.css, js/main.js
├── media/                     # uploaded images (local only; S3 on AWS)
└── docs/AWS_GUIDE.md
```

### How the pieces fit (simple explanation)

* **Model** = a database table written as a Python class (e.g. `Booking`).
* **View** = a Python function that handles a web request (e.g. "show my bookings").
* **Template** = the HTML page the view fills with data.
* **URL** = connects a web address (`/bookings/my/`) to a view.
* **Form** = checks what the user typed (validation) and saves it.

---------------------------------------------------------------------

## Part 2 – Install and run locally

You need **Python 3.10+** (check with `python --version`; on Windows try `py --version`).

```bash
# 1. open a terminal inside the capture_moments folder

# 2. create a virtual environment (a private box for this project's packages)
python -m venv venv

# 3. activate it
#    Windows (PowerShell):  venv\Scripts\Activate.ps1
#    Windows (cmd):         venv\Scripts\activate.bat
#    macOS / Linux:         source venv/bin/activate
#    (your prompt now starts with "(venv)")

# 4. install packages
pip install -r requirements.txt

# 5. create the database tables. Order matters – keep it exactly like this:
python manage.py makemigrations accounts photographers bookings
python manage.py migrate

# 6. create the photography categories + optional demo data
python manage.py seed_data --demo

# 7. create your admin login
python manage.py createsuperuser

# 8. start the website
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

**Demo accounts** (created by `seed_data --demo`, password for all: `Demo@12345`):
client `demo_client`; photographers `aarav_lens`, `meera_frames`, `rohan_clicks`, `sana_studio`.

Common problems
* `No module named django` → the virtual environment is not active (step 3) or step 4 was skipped.
* `no such table` → run step 5 again.
* Categories missing on the sign-up form → run step 6.
* Emails appear in the terminal window running `runserver` – that is intentional for local development.

---------------------------------------------------------------------

## Part 3 – Test everything

### A. Automated tests
```bash
python manage.py test
```
You should see `OK`. If something fails, the message shows which test and why – send it to your mentor/me.
The tests cover registration, role protection, search filters, booking validation (past date, blocked date,
bad duration, duplicates), accept/reject, double-accept protection, cancel, notifications and the admin dashboard.

### B. Manual checklist (use two browsers, or one normal + one private window)

| # | Do this | Expect |
|---|---------|--------|
| 1 | Open `/` | Dark/gold home page, categories, featured photographers |
| 2 | Sign up as a client (`/accounts/register/client/`) | Redirected to "My bookings" with a welcome message |
| 3 | Log out, sign up as a photographer | Redirected to the Portfolio page; categories are checkboxes |
| 4 | Photographer: upload 2–3 JPG/PNG images | Thumbnails appear; a `.pdf` or >5 MB file is refused |
| 5 | Photographer: Profile page → change price, add photo | "Profile updated" |
| 6 | Photographer: Availability → block a date 10 days ahead | Date shows grey on the calendar |
| 7 | Client: Find Photographers → filter by city, category, price, sort | List narrows correctly; "Clear" resets |
| 8 | Client: open a profile | Gallery (click opens large image), services, calendar |
| 9 | Client: Request a booking for a **blocked** date | Error: photographer not available |
| 10 | Client: Request a booking for **yesterday** | Error: choose a date from tomorrow onwards |
| 11 | Client: Request a valid booking | Success message; appears as **Pending** in My bookings |
| 12 | Photographer: bell shows **1**; Dashboard shows pending request | Yes |
| 13 | Photographer: click **Accept** | Moves to "Upcoming"; client's phone/email visible |
| 14 | Client: bell shows 1; status is **Accepted** | Yes |
| 15 | Another client tries the same date | Error: already booked; calendar shows red |
| 16 | Client: **Cancel booking** | Status Cancelled; photographer gets a notification |
| 17 | Log in with the superuser → **Admin Dashboard** | Counts, tabs for bookings/photographers/clients |
| 18 | Admin: deactivate a client | That client can no longer log in |
| 19 | While logged in as a client, open `/bookings/requests/` | Redirected away (no permission) |

---------------------------------------------------------------------

## Part 4 – Notes on design choices

* **One `User` table with a `role`** keeps login simple; photographers also get a linked `PhotographerProfile`.
* **Availability = blocked dates + accepted bookings.** Everyone is available by default; the photographer blocks
  days off. An accepted booking blocks that whole day (simple and clear for a college project).
  Pending requests do not block a day.
* **Price** is copied into the booking (`total_price = price_per_hour × hours`) when it is requested, so later price
  changes don't alter old bookings.
* **Notifications** are saved in the database (bell icon) and also e-mailed. Locally e-mails print in the terminal.
* **Security basics included:** passwords hashed by Django, CSRF protection on every form, state-changing actions
  accept POST only, users can only touch their own bookings, uploads are checked to be real images ≤ 5 MB.

## Part 5 – Known limitations (be ready to explain these in your viva)

* No online payment, no reviews/ratings, no chat.
* The calendar is day-level (no time-slot conflicts within a day).
* Email is console-only until you configure a real mail service (e.g. Amazon SES).
* SQLite is fine for one server and a demo; use PostgreSQL (e.g. Amazon RDS) for real traffic.

## Part 6 – AWS

See **`docs/AWS_GUIDE.md`**. Only do it after Parts 2 and 3 work locally.
