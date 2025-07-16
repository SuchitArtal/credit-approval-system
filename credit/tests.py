from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Customer, Loan



class CreditAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            age=30,
            monthly_salary=50000,
            approved_limit=1800000,
            current_debt=0,
            phone_number="9999999999"
        )

    def test_register_customer(self):
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "age": 28,
            "monthly_income": 60000,
            "phone_number": "8888888888"
        }
        response = self.client.post(reverse('customer-register'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Customer.objects.filter(phone_number="8888888888").exists())

    def test_register_customer_missing_field(self):
        data = {
            "first_name": "Jane",
            # "last_name" is missing
            "age": 28,
            "monthly_income": 60000,
            "phone_number": "8888888888"
        }
        response = self.client.post(reverse('customer-register'), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('last_name', response.data)

    def test_check_eligibility(self):
        data = {
            "customer_id": self.customer.id,
            "loan_amount": 100000,
            "interest_rate": 13.0,
            "tenure": 12
        }
        response = self.client.post(reverse('check-eligibility'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('approval', response.data)

    def test_create_loan(self):
        data = {
            "customer_id": self.customer.id,
            "loan_amount": 100000,
            "interest_rate": 13.0,
            "tenure": 12
        }
        response = self.client.post(reverse('create-loan'), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('loan_approved', response.data)
        if response.data['loan_approved']:
            self.assertIsNotNone(response.data['loan_id'])

    def test_view_loan(self):
        loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=100000,
            tenure=12,
            interest_rate=13.0,
            monthly_repayment=9000,
            emis_paid_on_time=0,
            start_date="2023-01-01",
            end_date="2024-01-01",
            is_approved=True
        )
        response = self.client.get(reverse('view-loan', args=[loan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], loan.id)

    def test_view_loan_not_found(self):
        response = self.client.get(reverse('view-loan', args=[9999]))
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.data)

    def test_view_loans(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=100000,
            tenure=12,
            interest_rate=13.0,
            monthly_repayment=9000,
            emis_paid_on_time=0,
            start_date="2023-01-01",
            end_date="2024-01-01",
            is_approved=True
        )
        response = self.client.get(reverse('view-loans', args=[self.customer.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_view_loans_customer_not_found(self):
        response = self.client.get(reverse('view-loans', args=[9999]))
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.data)
