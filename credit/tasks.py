import pandas as pd
from celery import shared_task
from .models import Customer, Loan
from django.db import transaction
from datetime import datetime

@shared_task
def ingest_customer_and_loan_data(customer_file_path, loan_file_path):
    # Ingest customers
    customer_df = pd.read_excel(customer_file_path)
    with transaction.atomic():
        for _, row in customer_df.iterrows():
            Customer.objects.update_or_create(
                id=row['Customer ID'],
                defaults={
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'monthly_salary': row['Monthly Salary'],
                    'approved_limit': row['Approved Limit'],
                    'current_debt': 0,
                    'age': row['Age'],
                    'phone_number': row['Phone Number'],
                }
            )
    # Ingest loans
    loan_df = pd.read_excel(loan_file_path)
    with transaction.atomic():
        for _, row in loan_df.iterrows():
            try:
                customer = Customer.objects.get(id=row['Customer ID'])
            except Customer.DoesNotExist:
                continue
            Loan.objects.update_or_create(
                id=row['Loan ID'],
                defaults={
                    'customer': customer,
                    'loan_amount': row['Loan Amount'],
                    'tenure': row['Tenure'],
                    'interest_rate': row['Interest Rate'],
                    'monthly_repayment': row['Monthly payment'],
                    'emis_paid_on_time': row['EMIs paid on Time'],
                    'start_date': pd.to_datetime(row['Date of Approval']).date() if not pd.isnull(row['Date of Approval']) else datetime.now().date(),
                    'end_date': pd.to_datetime(row['End Date']).date() if not pd.isnull(row['End Date']) else datetime.now().date(),
                    'is_approved': True,
                }
            ) 