from django.db import models

# Create your models here.

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_salary = models.PositiveIntegerField()
    approved_limit = models.PositiveIntegerField()
    current_debt = models.PositiveIntegerField(default=0)
    age = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id})"

class Loan(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.FloatField()
    tenure = models.PositiveIntegerField(help_text="Tenure in months")
    interest_rate = models.FloatField()
    monthly_repayment = models.FloatField()
    emis_paid_on_time = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Loan {self.id} for Customer {self.customer.id}"
