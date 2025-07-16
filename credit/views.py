from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegisterSerializer
from .models import Customer, Loan
from .serializers import (
    CustomerRegisterSerializer,
    CheckEligibilitySerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanSerializer,
    CreateLoanResponseSerializer,
    CustomerDetailSerializer,
    LoanDetailSerializer,
    LoanListItemSerializer
)
from datetime import datetime
from django.db import models

# Create your views here.

class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            response_data = CustomerRegisterSerializer(customer).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Gather all loans for this customer
        loans = Loan.objects.filter(customer=customer)
        now = datetime.now()
        current_year = now.year

        # Credit score calculation
        credit_score = 100
        total_emi = 0
        current_loans_sum = 0
        past_loans_paid_on_time = 0
        num_loans = loans.count()
        loan_activity_this_year = 0
        loan_approved_volume = 0

        for loan in loans:
            # If loan is ongoing, add to current loans sum and EMIs
            if loan.end_date >= now.date():
                current_loans_sum += loan.loan_amount
                total_emi += loan.monthly_repayment
            # Count loans paid on time
            if loan.emis_paid_on_time >= loan.tenure:
                past_loans_paid_on_time += 1
            # Loan activity in current year
            if loan.start_date.year == current_year:
                loan_activity_this_year += 1
            # Loan approved volume
            loan_approved_volume += loan.loan_amount

        # If sum of current loans > approved limit, credit score = 0
        if current_loans_sum > customer.approved_limit:
            credit_score = 0
        else:
            # Example scoring logic (customize as needed):
            if num_loans > 0:
                credit_score -= (num_loans * 5)  # Penalty for more loans
            credit_score += (past_loans_paid_on_time * 10)  # Reward for on-time
            credit_score += min(loan_activity_this_year * 5, 15)  # Cap activity bonus
            credit_score += min(loan_approved_volume / 100000, 20)  # Cap volume bonus
            credit_score = max(0, min(credit_score, 100))

        # If sum of all current EMIs > 50% of monthly salary, don’t approve any loans
        if total_emi + (loan_amount / tenure) > 0.5 * customer.monthly_salary:
            approval = False
            corrected_interest_rate = max(interest_rate, 16.0)
        else:
            # Approval logic based on credit score
            approval = False
            corrected_interest_rate = interest_rate
            if credit_score > 50:
                approval = True
            elif 50 >= credit_score > 30:
                if interest_rate > 12.0:
                    approval = True
                else:
                    corrected_interest_rate = 12.0
            elif 30 >= credit_score > 10:
                if interest_rate > 16.0:
                    approval = True
                else:
                    corrected_interest_rate = 16.0
            else:
                approval = False
                corrected_interest_rate = max(interest_rate, 16.0)

        # Calculate monthly installment (EMI) using compound interest formula
        r = corrected_interest_rate / (12 * 100)
        n = tenure
        emi = (loan_amount * r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else loan_amount / n

        response_data = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': round(emi, 2),
            'credit_score': credit_score  # Add this line for debugging
        }
        resp_serializer = CheckEligibilityResponseSerializer(response_data)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)

class CreateLoanView(APIView):
    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Reuse eligibility logic from CheckEligibilityView
        # (Copy the logic or refactor into a helper function for DRY code)
        loans = Loan.objects.filter(customer=customer)
        now = datetime.now()
        current_year = now.year
        credit_score = 100
        total_emi = 0
        current_loans_sum = 0
        past_loans_paid_on_time = 0
        num_loans = loans.count()
        loan_activity_this_year = 0
        loan_approved_volume = 0
        for loan in loans:
            if loan.end_date >= now.date():
                current_loans_sum += loan.loan_amount
                total_emi += loan.monthly_repayment
            if loan.emis_paid_on_time >= loan.tenure:
                past_loans_paid_on_time += 1
            if loan.start_date.year == current_year:
                loan_activity_this_year += 1
            loan_approved_volume += loan.loan_amount
        if current_loans_sum > customer.approved_limit:
            credit_score = 0
        else:
            if num_loans > 0:
                credit_score -= (num_loans * 5)
            credit_score += (past_loans_paid_on_time * 10)
            credit_score += min(loan_activity_this_year * 5, 15)
            credit_score += min(loan_approved_volume / 100000, 20)
            credit_score = max(0, min(credit_score, 100))
        if total_emi + (loan_amount / tenure) > 0.5 * customer.monthly_salary:
            approval = False
            corrected_interest_rate = max(interest_rate, 16.0)
            message = "Loan not approved: EMI exceeds 50% of monthly salary."
        else:
            approval = False
            corrected_interest_rate = interest_rate
            message = "Loan not approved due to credit score or interest rate."
            if credit_score > 50:
                approval = True
                message = "Loan approved successfully."
            elif 50 >= credit_score > 30:
                if interest_rate > 12.0:
                    approval = True
                    message = "Loan approved successfully."
                else:
                    corrected_interest_rate = 12.0
                    message = "Loan not approved: interest rate too low for credit score."
            elif 30 >= credit_score > 10:
                if interest_rate > 16.0:
                    approval = True
                    message = "Loan approved successfully."
                else:
                    corrected_interest_rate = 16.0
                    message = "Loan not approved: interest rate too low for credit score."
            else:
                approval = False
                corrected_interest_rate = max(interest_rate, 16.0)
                message = "Loan not approved due to low credit score."
        r = corrected_interest_rate / (12 * 100)
        n = tenure
        emi = (loan_amount * r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else loan_amount / n
        loan_id = None
        if approval:
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=interest_rate,
                monthly_repayment=emi,
                emis_paid_on_time=0,
                start_date=now.date(),
                end_date=(now.replace(month=now.month + tenure) if now.month + tenure <= 12 else now.replace(year=now.year + (now.month + tenure - 1) // 12, month=(now.month + tenure - 1) % 12 + 1)).date(),
                is_approved=True
            )
            loan_id = loan.id
        response_data = {
            'loan_id': loan_id,
            'customer_id': customer_id,
            'loan_approved': approval,
            'message': message,
            'monthly_installment': round(emi, 2) if approval else None
        }
        resp_serializer = CreateLoanResponseSerializer(response_data)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)

class ViewLoanDetail(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response({'detail': 'Loan not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ViewCustomerLoans(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
        loans = Loan.objects.filter(customer=customer, is_approved=True).exclude(emis_paid_on_time__gte=models.F('tenure'))
        serializer = LoanListItemSerializer(loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
