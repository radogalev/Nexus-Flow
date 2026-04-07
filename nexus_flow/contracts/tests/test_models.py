from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from accounts.models import CustomUser
from companies.models import Company
from contracts.models import Client, Contract, ContractService, Service


class ContractModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="manager@contract.com",
            password="StrongPass123!",
            first_name="Manager",
            last_name="Contract",
        )
        self.company = Company.objects.create(name="ContractCo", sector="tech", created_by=self.user)
        self.client_obj = Client.objects.create(name="Client A", email="client@test.com", company=self.company)

    def test_contract_days_until_expiry(self):
        contract = Contract.objects.create(
            title="C1",
            client=self.client_obj,
            company=self.company,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            signed_by=self.user,
        )
        self.assertEqual(contract.days_until_expiry, 1)

    def test_contract_recalculate_value(self):
        contract = Contract.objects.create(
            title="C2",
            client=self.client_obj,
            company=self.company,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            signed_by=self.user,
        )
        service1 = Service.objects.create(name="S1", unit_price=Decimal("100.00"), company=self.company)
        service2 = Service.objects.create(name="S2", unit_price=Decimal("50.00"), company=self.company)

        ContractService.objects.create(contract=contract, service=service1, quantity=2)
        ContractService.objects.create(contract=contract, service=service2, quantity=1)

        contract.recalculate_value()
        contract.refresh_from_db()
        self.assertEqual(contract.value, Decimal("250.00"))
