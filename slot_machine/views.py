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


class SlotMachineListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        customer_name = request.data.get("customer_name")
        phone_number = request.data.get("phone_number")
        region = request.data.get("region", "None")
        product_purchased = request.data.get("product_purchased")
        bill_number = request.data.get("bill_number")

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
            region=region,
            product_purchased=product_purchased,
            bill_number=bill_number,
        )

        self.assign_gift(customer)

        serializer = CustomerGiftSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ---------------- GIFT ASSIGNMENT ---------------- #
    def assign_gift(self, customer):
        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        # Update daily sales count
        sales_today, _ = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )
        sales_today.sales_count += 1
        sales_today.save()
        sales_count = sales_today.sales_count

        phone_model = customer.phone_model
        phone_number = customer.phone_number

        # ------------------ FIXED OFFERS ------------------ #
        fixed_offer = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            phone_number=phone_number,
            quantity__gt=0
        ).first()

        if fixed_offer:
            customer.gift.set(fixed_offer.gift.all())
            gift_names = ", ".join(
                [gift.name for gift in fixed_offer.gift.all()])
            customer.prize_details = f"Congratulations! You've won {gift_names}"
            customer.save()
            fixed_offer.quantity -= 1
            fixed_offer.save()
            return

        # ------------------ ELECTRONIC OFFERS ------------------ #
        electronic_offers = ElectronicsShopOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            start_date__lte=today_date,
            end_date__gte=today_date,
            daily_quantity__gt=0,
        )

        # Step 1: collect offers that match condition and phone model
        matching_offers = [
            offer for offer in electronic_offers
            if self.check_offer_condition(offer, sales_count, customer.region)
            and self.check_validto_condition(offer, phone_model)
        ]

        if not matching_offers:
            customer.prize_details = "Thank you for your purchase!"
            customer.save()
            return

        # Step 2: sort offers by condition value ascending
        matching_offers.sort(key=lambda o: int(o.offer_condition_value))

        # Step 3: group offers by condition value
        offers_by_condition = {}
        for offer in matching_offers:
            cv = int(offer.offer_condition_value)
            offers_by_condition.setdefault(cv, []).append(offer)

        assigned_gifts = []

        # Step 4: assign gifts for all condition values up to the highest met
        highest_cv_met = max(offers_by_condition.keys())

        for cv in sorted(offers_by_condition.keys()):
            if cv > highest_cv_met:
                continue  # skip condition values above highest met

            offers = offers_by_condition[cv]

            # Group gifts by category (major, minor, grand)
            offers_by_category = {}
            for offer in offers:
                for gift in offer.gift.all():
                    offers_by_category.setdefault(
                        gift.category, []).append((offer, gift))

            # Assign best gift per category (lowest assigned ratio)
            for category, gift_options in offers_by_category.items():
                best_gift = None
                lowest_ratio = None

                for offer, gift in gift_options:
                    already_assigned = Customer.objects.filter(
                        date_of_purchase=today_date,
                        gift=gift
                    ).count()

                    total_quantity = max(offer.daily_quantity, 1)
                    assigned_ratio = already_assigned / total_quantity

                    if lowest_ratio is None or assigned_ratio < lowest_ratio:
                        lowest_ratio = assigned_ratio
                        best_gift = gift

                if best_gift:
                    customer.gift.add(best_gift)
                    assigned_gifts.append(best_gift)

        # Step 5: save prize details
        if assigned_gifts:
            gift_names = ", ".join([gift.name for gift in assigned_gifts])
            customer.prize_details = f"Congratulations! You've won {gift_names}"
        else:
            customer.prize_details = "Thank you for your purchase!"

        customer.save()

    # ---------------- OFFER CHECKING ---------------- #

    def check_offer_condition(self, offer, sales_count, region="None"):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        if offer.has_region_limit:
            if region == "None" or region == "Other":
                return False

            region_counts = {}
            for gift in offer.gift.all():
                region_counts[region] = Customer.objects.filter(
                    region=region,
                    gift=gift,
                    date_of_purchase=today_date
                ).count()

            max_gifts_per_region = 5  # configurable
            if region_counts.get(region, 0) >= max_gifts_per_region:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
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
