from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Organization
from offers.models import Customer, FixOffer, GiftItem, LuckyDrawSystem


class SlotMachineAPITests(APITestCase):
    def setUp(self):
        # Create an Organization
        self.organization = Organization.objects.create(
            name="Test Org",
            email="test@org.com",
            phone_number="1234567890",
            address="123 Street",
        )

        # Create LuckyDrawSystem
        self.lucky_draw = LuckyDrawSystem.objects.create(
            organization=self.organization,
            name="Test Draw",
            type="Electronics Shop",
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=5),
            uuid_key="test-uuid",
        )

        # Create GiftItems
        self.gift1 = GiftItem.objects.create(
            lucky_draw_system=self.lucky_draw, name="Gift One", category="minor"
        )
        self.gift2 = GiftItem.objects.create(
            lucky_draw_system=self.lucky_draw, name="Gift Two", category="minor"
        )

        self.url = reverse("customer-list-create")

    def test_create_customer_success(self):
        data = {
            "lucky_draw_system": self.lucky_draw.id,
            "customer_name": "John Doe",
            "phone_number": "9876543210",
            "region": "Eastern Region",
            "product_purchased": "TV",
            "bill_number": "BILL001",
        }

        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Customer.objects.count() == 1

        customer = Customer.objects.get()
        assert customer.customer_name == "John Doe"
        assert customer.phone_number == "9876543210"
        assert customer.region == "Eastern Region"

    def test_retry_customer_success(self):
        # First create a customer
        customer = Customer.objects.create(
            lucky_draw_system=self.lucky_draw,
            customer_name="John Doe",
            phone_number="9876543210",
            region="Eastern Region",
            product_purchased="TV",
            bill_number="BILL001",
        )
        customer.gift.add(self.gift1)
        customer.save()

        # Define a fixed offer for the phone number so they win gift2 on retry
        FixOffer.objects.create(
            lucky_draw_system=self.lucky_draw, phone_number="9876543210", quantity=1
        ).gift.add(self.gift2)

        data = {
            "lucky_draw_system": self.lucky_draw.id,
            "phone_number": "9876543210",
            "retry": True,
            "customer_name": "John Updated",
            "region": "Western Region",
        }

        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert Customer.objects.count() == 1  # No new customer created

        customer.refresh_from_db()
        assert customer.customer_name == "John Updated"
        assert customer.region == "Western Region"
        # Gift should be updated from gift1 to gift2
        assert self.gift2 in customer.gift.all()
        assert self.gift1 not in customer.gift.all()

    def test_retry_customer_not_found(self):
        data = {
            "lucky_draw_system": self.lucky_draw.id,
            "phone_number": "0000000000",
            "retry": True,
        }
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            response.data["error"]
            == "Customer not found with this phone number and lucky draw system."
        )

    def test_retry_without_phone_number(self):
        data = {
            "lucky_draw_system": self.lucky_draw.id,
            "retry": True,
        }
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "phone_number is required for retry."
