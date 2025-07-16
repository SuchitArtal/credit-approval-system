# Credit Approval System Backend

A robust, production-ready backend for a Credit Approval System built with Django 4+, Django Rest Framework, PostgreSQL, Docker, Celery, and Redis.

## Features
- **Django 4+** and **DRF** for scalable REST APIs
- **PostgreSQL** for reliable data storage
- **Dockerized**: The entire application (Django, PostgreSQL, Redis, Celery worker) runs from a single `docker-compose up --build` command
- **Celery + Redis** for background tasks (data ingestion)
- **Modular, well-organized codebase** with clear separation of concerns (models, serializers, views, tasks, tests)
- **Comprehensive unit tests** for all major endpoints (see `credit/tests.py`)

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd alemeno
```

### 2. Build and run everything with Docker Compose
```bash
docker-compose up --build
```
- The API will be available at `http://localhost:8000/`
- The PostgreSQL database will be available at `localhost:5432`
- Redis and Celery worker are started automatically

### 3. Apply Migrations & Create Superuser
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 4. Collect Static Files (for Django Admin CSS)
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 5. Access Django Admin
- Visit [http://localhost:8000/admin/](http://localhost:8000/admin/)
- Log in with your superuser credentials

### 6. Data Ingestion (Excel to Database)
- Place your `customer_data.xlsx` and `loan_data.xlsx` files in the project root.
- Start a Celery worker in a new terminal:
  ```bash
  docker-compose exec web celery -A credit_approval_system worker --loglevel=info
  ```
- In another terminal, open the Django shell:
  ```bash
  docker-compose exec web python manage.py shell
  ```
  Then run:
  ```python
  from credit.tasks import ingest_customer_and_loan_data
  ingest_customer_and_loan_data('/app/customer_data.xlsx', '/app/loan_data.xlsx')
  ```
- Refresh the Django admin to see ingested data.

### 7. Run Unit Tests
```bash
docker-compose exec web python manage.py test credit
```
- All major endpoints and business logic are covered by tests in `credit/tests.py`.

## API Usage

### 1. Register Customer (`/customer/register`)
- **POST** `/customer/register`
- **Request Body:**
  ```json
  {
    "first_name": "Priya",
    "last_name": "Sharma",
    "age": 29,
    "monthly_income": 80000,
    "phone_number": "9123456789"
  }
  ```
- **Response:**
  ```json
  {
    "id": 6,
    "first_name": "Priya",
    "last_name": "Sharma",
    "name": "Priya Sharma",
    "age": 29,
    "monthly_income": 80000,
    "approved_limit": 2900000,
    "phone_number": "9123456789"
  }
  ```

### 2. Check Eligibility (`/check-eligibility`)
- **POST** `/check-eligibility`
- **Request Body:**
  ```json
  {
    "customer_id": 5,
    "loan_amount": 200000,
    "interest_rate": 13.0,
    "tenure": 24
  }
  ```
- **Response:**
  ```json
  {
    "customer_id": 5,
    "approval": true,
    "interest_rate": 13.0,
    "corrected_interest_rate": 13.0,
    "tenure": 24,
    "monthly_installment": 9508.36
  }
  ```

### 3. Create Loan (`/create-loan`)
- **POST** `/create-loan`
- **Request Body:**
  ```json
  {
    "customer_id": 5,
    "loan_amount": 200000,
    "interest_rate": 13.0,
    "tenure": 24
  }
  ```
- **Response (approved):**
  ```json
  {
    "loan_id": 123,
    "customer_id": 5,
    "loan_approved": true,
    "message": "Loan approved successfully.",
    "monthly_installment": 9508.36
  }
  ```
- **Response (not approved):**
  ```json
  {
    "loan_id": null,
    "customer_id": 5,
    "loan_approved": false,
    "message": "Loan not approved due to low credit score.",
    "monthly_installment": null
  }
  ```

### 4. View Loan (`/view-loan/<loan_id>`)
- **GET** `/view-loan/1`
- **Response:**
  ```json
  {
    "id": 1,
    "customer": {
      "id": 5,
      "first_name": "Abdul",
      "last_name": "Lopez",
      "phone_number": "9175345317",
      "age": 40
    },
    "loan_amount": 200000,
    "interest_rate": 13.0,
    "is_approved": true,
    "monthly_repayment": 9508.36,
    "tenure": 24
  }
  ```

### 5. View All Loans for a Customer (`/view-loans/<customer_id>`)
- **GET** `/view-loans/5`
- **Response:**
  ```json
  [
    {
      "id": 1,
      "loan_amount": 200000,
      "is_approved": true,
      "interest_rate": 13.0,
      "monthly_repayment": 9508.36,
      "repayments_left": 20
    }
  ]
  ```

#### Eligibility & Approval Business Logic
- Credit score is calculated based on:
  - Past loans paid on time
  - Number of loans taken in the past
  - Loan activity in the current year
  - Loan approved volume
  - If sum of current loans > approved limit, credit score = 0
- Approval rules:
  - If credit_rating > 50: approve loan
  - If 50 >= credit_rating > 30: approve only if interest rate > 12%
  - If 30 >= credit_rating > 10: approve only if interest rate > 16%
  - If credit_rating <= 10: do not approve
  - If sum of all current EMIs > 50% of monthly salary, do not approve
  - If the interest rate does not match the slab, a corrected interest rate is suggested in the response
- EMI is calculated using the compound interest formula.

## Troubleshooting
- If you see missing static files in the admin, ensure you have run `collectstatic` and mapped the static volume in `docker-compose.yml`.
- If you get `KeyError` during ingestion, check that your Excel column names match exactly what the ingestion code expects.
- If you add new Python dependencies, update `requirements.txt` and rebuild your containers.

## Code Quality & Organization
- The codebase is modular and follows Django best practices:
  - **Models**: All data models in `credit/models.py`
  - **Serializers**: All input/output validation in `credit/serializers.py`
  - **Views**: All business logic and API endpoints in `credit/views.py`
  - **Tasks**: Background ingestion logic in `credit/tasks.py`
  - **Tests**: Comprehensive unit tests in `credit/tests.py`
- Responsibilities are clearly separated for maintainability and scalability.
