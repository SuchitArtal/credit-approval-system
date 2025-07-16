from rest_framework import serializers
from .models import Customer
from .models import Loan

class CustomerRegisterSerializer(serializers.ModelSerializer):
    monthly_income = serializers.IntegerField(write_only=True)
    name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number'
        ]
        read_only_fields = ['id', 'approved_limit', 'name']

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def create(self, validated_data):
        monthly_income = validated_data.pop('monthly_income')
        # Calculate approved_limit: 36 * monthly_income, rounded to nearest lakh
        approved_limit = int(round((36 * monthly_income) / 100000.0) * 100000)
        customer = Customer.objects.create(
            approved_limit=approved_limit,
            monthly_salary=monthly_income,
            current_debt=0,
            **validated_data
        )
        return customer 

class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField() 

class CreateLoanSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField(allow_null=True) 

class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']

class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerDetailSerializer(read_only=True)
    class Meta:
        model = Loan
        fields = [
            'id', 'customer', 'loan_amount', 'interest_rate', 'is_approved', 'monthly_repayment', 'tenure'
        ]

class LoanListItemSerializer(serializers.ModelSerializer):
    repayments_left = serializers.SerializerMethodField()
    class Meta:
        model = Loan
        fields = [
            'id', 'loan_amount', 'is_approved', 'interest_rate', 'monthly_repayment', 'repayments_left'
        ]
    def get_repayments_left(self, obj):
        return max(obj.tenure - obj.emis_paid_on_time, 0) 