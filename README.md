# Personal Finance Tracker

A full-stack web application built with **Django** and **PostgreSQL** that allows users to track income and expenses, manage monthly budgets, and view financial summaries with live currency conversion.

This project was developed as part of the **Final Full Stack Web Application Development Assignment (40%)**.

---

## Project Overview

The Personal Finance Tracker enables authenticated users to:

- Register and log in securely
- Record income and expense transactions
- Categorise transactions
- Set monthly budgets (overall or per category)
- View a personalised dashboard with month-to-date totals
- Convert financial totals into different currencies using a live external API

The application focuses on clean backend integration, database design, and deployment readiness, without using React (Django templates are used instead).

---

## Core Features

### User Authentication
- User registration, login, and logout
- Passwords securely hashed using Django’s authentication system
- Login-protected dashboard and feature pages

### Transactions (CRUD)
- Create, view, update, and delete transactions
- Transactions can be income or expense
- Categorised per user
- Month-to-date summaries

### Budgets
- Set monthly budgets
- Overall budget or category-specific budgets
- Budget overview page showing spending vs budget

### Dashboard
- Personalised dashboard for each user
- Monthly income, expenses, and net balance
- Currency selection (EUR / USD / GBP)
- Graceful handling of unavailable API data

### External API Integration
- Live currency exchange rates using the **Frankfurter API**
- Converts stored EUR amounts into selected display currency
- Cached to reduce unnecessary API requests

### Automated Testing
- Django `TestCase`-based test suite
- Tests cover:
  - User registration and login
  - Access control for protected pages
  - Transaction creation
  - Budget creation

---

## Technology Stack

### Backend
- Python 3
- Django
- Django ORM

### Database
- PostgreSQL (local development via pgAdmin 4)
- Render-compatible configuration for production

### Frontend
- Django Templates
- Bootstrap 5 (responsive design)

### Other Tools
- Git & GitHub (feature branches + commits)
- External API: Frankfurter (currency exchange) (free no API key needed)
- Render (deployment ready)

---

## Installation & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/Bre0409/final_assignment_finance_tracker.git
cd personal_finance_tracker

Step 2: Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   

Step 3: Install requirements
pip install -r requirements.txt

Step 4: Environment variables
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/personal_finance_tracker?sslmode=disable

Step 5: Apply database migrations
python manage.py migrate

Step 6: Create a superuser
python manage.py createsuperuser

Step 7: Start the development server
python manage.py runserver

Open the application in a browser:
http://127.0.0.1:8000/

Step 8: Access the application

Register a new user account

Log in to access the dashboard

Add transactions and budgets

Change display currency from the dashboard dropdown


Running Automated Tests

Automated tests are included and can be run using:

python manage.py test


All tests should pass before deployment.


Deployment Notes

The application is configured for deployment on Render using:

Gunicorn

PostgreSQL

Environment variables for secrets and database credentials

Local PostgreSQL development mirrors the production setup to ensure a smooth deployment process.

Project Status

Core functionality complete

External API integration complete

Automated testing complete

Git version control with feature branches

Deployment-ready configuration

Author

Brendan

Final Full Stack Web Application Development Assignment

License

This project is for educational purposes only.