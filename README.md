# EVA Atelier

**A Minimalist Luxury Handbag E-Commerce Platform**

EVA Atelier is a modern e-commerce web application designed for a premium handbag brand. It combines a clean, cream-and-white storefront with a Python backend, product management, customer authentication, order processing, and payment integration.

**Live Website:** https://eva-atelier.vercel.app  
**GitHub Repository:** https://github.com/prastut101/Eva-Atelier

---

## Overview

EVA Atelier aims to deliver a refined online shopping experience through a minimalist interface, organized product listings, and a backend architecture designed to support essential e-commerce operations.

The application includes a customer-facing storefront and administrative functionality for managing products, categories, orders, and store analytics.

## Features

### Customer Storefront
- Minimalist, premium-inspired design.
- Product listings and individual product pages.
- Product categories and browsing.
- Shopping cart functionality.
- Customer authentication.
- Wishlist functionality.
- Order tracking interface.

### Administration
- Administrative interface.
- Product and category management.
- Order management.
- Sales and store analytics interface.

### Backend and Security
- REST API built with FastAPI.
- SQLAlchemy database integration.
- Database schema migrations with Alembic.
- Password hashing with bcrypt.
- JWT-based authentication.
- Environment-based configuration for sensitive credentials.

### Payments
- Khalti payment gateway integration.
- Payment initiation and lookup functionality.
- Payment configuration through environment variables.

*Payment availability depends on valid credentials, gateway configuration, and successful payment verification.*

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| ORM | SQLAlchemy |
| Database | PostgreSQL / SQLite fallback |
| Database migrations | Alembic |
| Authentication | JWT, OAuth2-compatible flows |
| Password hashing | bcrypt |
| Payment integration | Khalti |
| Deployment | Vercel |
| Version control | Git and GitHub |

## Project Structure

```text
EVA/
├── app.py
├── create_admin.py
├── requirements.txt
├── .gitignore
├── backend/
│   └── app/
│       ├── main.py
│       ├── auth.py
│       ├── database.py
│       ├── models/
│       ├── schemas/
│       ├── routers/
│       │   ├── analytics.py
│       │   ├── categories.py
│       │   ├── orders.py
│       │   ├── payments.py
│       │   ├── product_images.py
│       │   └── products.py
│       ├── services/
│       │   ├── email.py
│       │   └── khalti.py
│       ├── utils/
│       │   └── auth.py
│       └── migrations/
└── frontend/
    ├── admin/
    ├── static/
    │   ├── css/
    │   ├── images/
    │   └── js/
    └── templates/
```

## Prerequisites

Install the following before running the project:

- Python 3.10 or later, compatible with the installed dependencies.
- pip.
- Git.
- A PostgreSQL database for a persistent production database, or SQLite for local development.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/prastut101/Eva-Atelier.git
cd Eva-Atelier
```

### 2. Create a virtual environment

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root. Do not commit this file to GitHub.

Example configuration:

```dotenv
SECRET_KEY=replace_with_a_secure_random_secret
DATABASE_URL=sqlite:///./eva_atelier.db
KHALTI_SECRET_KEY=
KHALTI_BASE_URL=https://dev.khalti.com/api/v2
```

**Important:**
- Generate a strong, unique `SECRET_KEY`.
- Use the correct `DATABASE_URL` for your database.
- Add valid Khalti credentials only when payment integration is required.
- Keep production credentials in your hosting provider's environment settings.
- Never commit real credentials or passwords.

The example uses SQLite for local development. Your production deployment may use PostgreSQL.

### 5. Initialize the database

Apply the existing Alembic migrations:

```bash
alembic -c backend/app/alembic.ini upgrade head
```

If the command fails, check the Alembic configuration, Python import path, and database connection settings before proceeding.

### 6. Start the application

From the project root, run:

```bash
uvicorn backend.app.main:app --reload
```

The local API should be available at:

- **Application:** http://127.0.0.1:8000
- **Interactive API documentation:**
- **Alternative API documentation:** 

The exact endpoints available depend on the routes registered in the application.

## Admin Setup

The project includes a `create_admin.py` script for administrative account setup.

Before running it, review the script to understand how it creates accounts and handles passwords. Ensure that it uses the intended database and does not contain hardcoded production credentials.

If the script is designed to create an administrator from your environment or command-line inputs, run:

```bash
python create_admin.py
```

Use a unique, strong administrator password. Do not publish default credentials or share administrative login details.

## Khalti Payment Configuration

The application includes a Khalti payment service.

To configure it:

1. Obtain the appropriate credentials from Khalti.
2. Configure `KHALTI_SECRET_KEY` in your local environment or deployment settings.
3. Set `KHALTI_BASE_URL` to the appropriate gateway environment.
4. Test payment initiation and verification using the gateway's supported test environment.
5. Verify payment status on the server before marking an order as paid.

Do not rely exclusively on frontend redirects or client-submitted payment status to confirm a successful transaction.

## Database Configuration

The application supports database configuration through `DATABASE_URL`.

**SQLite for development**

```dotenv
DATABASE_URL=sqlite:///./eva_atelier.db
```

**PostgreSQL for production**

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Replace the PostgreSQL placeholders with your actual connection details. Keep the real connection string private.

Use Alembic migrations to manage database schema changes. Back up production data before applying migrations that may modify existing records.

## Deployment

The project is deployed at:

https://eva-atelier.vercel.app

For a new deployment or redeployment:

1. Connect the GitHub repository to your Vercel project.
2. Configure the required environment variables in Vercel.
3. Ensure the deployment configuration uses the correct FastAPI application entry point.
4. Configure a persistent production database.
5. Apply the required migrations.
6. Test authentication, product loading, administration, and payment flows.
7. Review deployment logs and verify the production application.

Do not assume that a local SQLite database or uploaded local files automatically persist in a serverless deployment. Use an appropriate persistent database and storage service where required.

## Security Practices

- Never commit `.env` files, API keys, database credentials, or private tokens.
- Use strong, randomly generated JWT signing keys.
- Hash passwords before storing them.
- Restrict administrative operations to authorized users.
- Validate payment status on the server.
- Keep dependencies updated.
- Avoid exposing sensitive error details in production.
- Rotate credentials immediately if they are exposed.
- Remember that removing a secret in a later commit does not remove it from earlier Git history.

## Development Workflow

To publish future changes:

```bash
git add -A
git commit -m "Describe your changes"
git push
```

Review the staged files before committing, especially when changing environment configuration or adding new files.

## Future Improvements

Potential improvements include:

- Automated unit and integration testing.
- More comprehensive product inventory management.
- Persistent image storage.
- Transactional email notifications.
- Enhanced analytics and reporting.
- Improved accessibility and performance.
- Automated deployment checks.
- Additional payment and order reconciliation safeguards.

## License

No license has been specified yet. Unless a license is added to this repository, reuse and redistribution remain subject to applicable copyright law.

---

**EVA Atelier — Every carry tells a story.**
