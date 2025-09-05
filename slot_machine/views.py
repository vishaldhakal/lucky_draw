from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from offers.models import Customer, IMEINO
from offers.serializers import CustomerSerializer, CustomerGiftSerializer
from django.utils import timezone
from offers.models import LuckyDrawSystem
from offers.models import FixOffer, MobilePhoneOffer, ElectronicsShopOffer, Sales

# Create your views here.


class SlotMachineListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    # def get_queryset(self):
    #     return Customer.objects.filter(
    #         lucky_draw_system__organization=self.request.user.organization
    #     )

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
        )

        if region:
            customer.region = region

        self.assign_gift(customer)

        serializer = CustomerGiftSerializer(customer)
        data = serializer.data
        if (customer.gift is not None) and (customer.gift.image != ""):
            data["gift"]["image"] = request.build_absolute_uri(
                data["gift"]["image"])
        return Response(data, status=status.HTTP_201_CREATED)

    def assign_gift(self, customer):
        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        sales_today, created = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )

        """ if not Sales.objects.filter(date=today_date, lucky_draw_system=lucky_draw_system).exists():
            sales_today = Sales.objects.create(
                date=today_date,
                lucky_draw_system=lucky_draw_system,
                sales_count=0
            )
        else:
            sales_today = Sales.objects.get(date=today_date, lucky_draw_system=lucky_draw_system,sales_count=0) """

        sales_today.sales_count += 1
        sales_today.save()

        sales_count = sales_today.sales_count
        phone_model = customer.phone_model
        phone_number = customer.phone_number

        fixed_offer = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw_system, phone_number=phone_number, quantity__gt=0
        ).first()

        if fixed_offer:
            customer.gift = fixed_offer.gift
            customer.prize_details = (
                f"Congratulations! You've won {fixed_offer.gift.name}"
            )
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
            condition_met = self.check_offer_condition(offer, sales_count)
            validto_check = self.check_validto_condition(offer, phone_model)

            if condition_met and validto_check:
                customer.gift = offer.gift
                customer.prize_details = f"Congratulations! You've won {offer.gift.name} from our Electronics Shop Offer!"
                customer.save()

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

            region_counts = {
                "Centeral Region": Customer.objects.filter(region="Centeral Region", gift=offer.gift).count(),
                "Eastern Region": Customer.objects.filter(region="Eastern Region", gift=offer.gift).count(),
                "Western Region": Customer.objects.filter(region="Western Region", gift=offer.gift).count(),
            }

            min_count = min(region_counts.values())

            if region_counts[region] > min_count:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
            todayscount = Customer.objects.filter(
                date_of_purchase=today_date, gift=offer.gift
            ).count()
            return (
                sales_count % int(offer.offer_condition_value) == 0
                and todayscount < offer.daily_quantity
            )
        elif offer.type_of_offer == "At certain sale position":
            return str(sales_count) in offer.sale_numbers
        return (
            False  # If the offer type doesn't match any condition, it's not applicable
        )

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True  # If there are no valid conditions, the offer is applicable to all devices

        for condition in offer.valid_condition.all():
            if phone_model.startswith(condition.condition):
                return True

        return False  # If there are valid conditions but no match, the offer is not valid for this phone model

        # if hasattr(offer, "valid_condition"):
        #     conditions = offer.valid_condition.all()
        #     return not conditions or any(
        #         phone_model.startswith(cond.condition) for cond in conditions
        #     )
        # return True  # If there's no valid_condition, assume it's valid for all
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from offers.models import GiftItem
from offers.serializers import GiftItemSerializer

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