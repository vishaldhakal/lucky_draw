from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from offers.models import Customer, IMEINO
from offers.serializers import CustomerSerializer, CustomerGiftSerializer
from django.utils import timezone
from offers.models import LuckyDrawSystem
from offers.models import FixOffer, MobilePhoneOffer, ElectronicsShopOffer, Sales
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from offers.models import GiftItem
from offers.serializers import GiftItemSerializer
# Create your views here.


class SlotMachineListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        customer_name = request.data.get("customer_name")
        phone_number = request.data.get("phone_number")
        email = request.data.get("email")
        region = request.data.get("region", "None")

        try:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
        except LuckyDrawSystem.DoesNotExist:
            return Response(
                {"error": "Lucky Draw System not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        customer = Customer.objects.create(
            lucky_draw_system=lucky_draw,
            customer_name=customer_name,
            phone_number=phone_number,
            email=email,
            region=region,
        )

        self.assign_gift(customer)

        serializer = CustomerGiftSerializer(customer)
        data = serializer.data

        return Response(data, status=status.HTTP_201_CREATED)

    def assign_gift(self, customer):
        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        sales_today, created = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )

        sales_today.sales_count += 1
        sales_today.save()

        sales_count = sales_today.sales_count
        phone_model = customer.phone_model
        phone_number = customer.phone_number

        # Check Fixed Offers first (now supports multiple gifts)
        fixed_offer = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            phone_number=phone_number,
            quantity__gt=0
        ).first()

        if fixed_offer:
            # Assign all gifts from the fixed offer
            customer.gift.set(fixed_offer.gift.all())
            gift_names = ", ".join(
                [gift.name for gift in fixed_offer.gift.all()])
            customer.prize_details = f"Congratulations! You've won {gift_names}"
            customer.save()
            fixed_offer.quantity -= 1
            fixed_offer.save()
            return

        # Check Electronic Shop Offers
        electronic_offers = ElectronicsShopOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            start_date__lte=today_date,
            end_date__gte=today_date,
            daily_quantity__gt=0,
        )

        for offer in electronic_offers:
            condition_met = self.check_offer_condition(
                offer, sales_count, customer.region)
            validto_check = self.check_validto_condition(offer, phone_model)

            if condition_met and validto_check:
                # Assign all gifts from the offer
                customer.gift.set(offer.gift.all())
                gift_names = ", ".join(
                    [gift.name for gift in offer.gift.all()])
                customer.prize_details = f"Congratulations! You've won {gift_names} from our Electronics Shop Offer!"
                customer.save()

                # Decrease daily quantity
                offer.daily_quantity -= 1
                offer.save()
                return

        # If no gift assigned
        customer.prize_details = "Thank you for your purchase!"
        customer.save()

    def check_offer_condition(self, offer, sales_count, region="None"):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        if offer.has_region_limit:
            if region == "None" or region == "Other":
                return False

            # For offers with multiple gifts, check region balance for all gifts
            region_counts = {}
            for gift in offer.gift.all():
                region_counts[region] = Customer.objects.filter(
                    region=region,
                    gift=gift,
                    date_of_purchase=today_date
                ).count()

            # You can implement your region limiting logic here
            # For example, limit total gifts per region per day
            max_gifts_per_region = 5  # Configure this as needed
            if region_counts.get(region, 0) >= max_gifts_per_region:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
            # Check how many customers have received gifts from this offer today
            todays_gift_count = Customer.objects.filter(
                date_of_purchase=today_date,
                gift__in=offer.gift.all()
            ).distinct().count()

            return (
                sales_count % int(offer.offer_condition_value) == 0
                and todays_gift_count < offer.daily_quantity
            )
        elif offer.type_of_offer == "At certain sale position":
            return str(sales_count) in offer.sale_numbers

        return False

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True

        for condition in offer.valid_condition.all():
            if phone_model and phone_model.startswith(condition.condition):
                return True

        return False


@api_view(["GET"])
def GetGifts(request):
    luck_draw_system_id = request.GET.get("lucky_draw_system")
    if not luck_draw_system_id:
        return Response(
            {"error": "lucky_draw_system parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    gifts = GiftItem.objects.all()
    serializer = GiftItemSerializer(gifts, many=True)
    return Response(serializer.data)
