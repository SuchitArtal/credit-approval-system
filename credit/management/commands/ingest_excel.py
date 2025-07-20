from django.core.management.base import BaseCommand
from credit.tasks import ingest_customer_and_loan_data
import os

class Command(BaseCommand):
    help = 'Trigger Celery task to ingest customer and loan data from Excel files.'

    def handle(self, *args, **options):
        customer_file = '/app/customer_data.xlsx'
        loan_file = '/app/loan_data.xlsx'
        if not os.path.exists(customer_file) or not os.path.exists(loan_file):
            self.stdout.write(self.style.WARNING('Excel files not found, skipping ingestion.'))
            return
        ingest_customer_and_loan_data.delay(customer_file, loan_file)
        self.stdout.write(self.style.SUCCESS('Triggered ingestion of customer and loan data.')) 