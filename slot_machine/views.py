from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from offers.models import (
    Customer,
    ElectronicsShopOffer,
    FixOffer,
    GiftItem,
    LuckyDrawSystem,
    Sales,
)
from offers.serializers import (
    CustomerGiftSerializer,
    CustomerSerializer,
    GiftItemSerializer,
)

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
        retry = request.data.get("retry")

        if isinstance(retry, str):
            retry = retry.lower() in ("true", "1")
        elif not isinstance(retry, bool):
            retry = False

        # Validate that the Lucky Draw System exists
        try:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
        except LuckyDrawSystem.DoesNotExist:
            return Response(
                {"error": "Lucky Draw System not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if retry:
            if not phone_number:
                return Response(
                    {"error": "phone_number is required for retry."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            customer = (
                Customer.objects
                .filter(phone_number=phone_number, lucky_draw_system=lucky_draw)
                .order_by("-id")
                .first()
            )
            if not customer:
                return Response(
                    {
                        "error": "Customer not found with this phone number and lucky draw system."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Clear old gifts
            customer.gift.clear()

            # Update customer details if provided
            if customer_name:
                customer.customer_name = customer_name
            if region and region != "None":
                customer.region = region
            if product_purchased:
                customer.product_purchased = product_purchased
            if bill_number:
                customer.bill_number = bill_number
            customer.save()
        else:
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
        data = serializer.data
        # Build absolute URL for gift image, handling both dict and list serializer outputs
        gift_data = data.get("gift")
        if isinstance(gift_data, dict):
            image = gift_data.get("image")
            if image:
                gift_data["image"] = request.build_absolute_uri(image)
        elif isinstance(gift_data, list) and gift_data:
            image = (
                gift_data[0].get("image") if isinstance(gift_data[0], dict) else None
            )
            if image:
                gift_data[0]["image"] = request.build_absolute_uri(image)

        status_code = status.HTTP_200_OK if retry else status.HTTP_201_CREATED
        return Response(data, status=status_code)

    # ---------------- GIFT ASSIGNMENT ---------------- #
    def assign_gift(self, customer):
        import random  # Natively imported for controlled tie-breaking

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
            quantity__gt=0,
        ).first()

        if fixed_offer:
            customer.gift.set(fixed_offer.gift.all())
            gift_names = ", ".join([gift.name for gift in fixed_offer.gift.all()])
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
            offer
            for offer in electronic_offers
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
        assigned_categories = set()

        # Step 4: assign gifts for all condition values up to the highest met
        highest_cv_met = max(offers_by_condition.keys())

        for cv in sorted(offers_by_condition.keys()):
            if cv > highest_cv_met:
                continue

            offers = offers_by_condition[cv]

            # Group gifts by category (major, minor, grand)
            offers_by_category = {}
            for offer in offers:
                for gift in offer.gift.all():
                    offers_by_category.setdefault(gift.category, []).append((
                        offer,
                        gift,
                    ))

            # Assign best gift per category (Fixed Two-Pass Ratio Balancing)
            for category, gift_options in offers_by_category.items():
                if category in assigned_categories:
                    continue

                # Pass 1: Calculate metrics and collect valid candidates that haven't hit caps
                valid_options = []
                for offer, gift in gift_options:
                    already_assigned = Customer.objects.filter(
                        date_of_purchase=today_date, gift=gift
                    ).count()

                    target_capacity = max(offer.daily_quantity, 1)

                    # Hard cutoff check
                    if already_assigned >= target_capacity:
                        continue

                    assigned_ratio = already_assigned / target_capacity
                    valid_options.append((gift, assigned_ratio))

                if not valid_options:
                    continue

                # Pass 2: Identify absolute lowest ratio baseline
                true_lowest_ratio = min(item[1] for item in valid_options)

                # Pass 3: Isolate options sitting cleanly within the 0.01 tolerance window
                tolerance = 0.01
                best_candidates = [
                    gift
                    for gift, ratio in valid_options
                    if ratio <= (true_lowest_ratio + tolerance)
                ]

                # Pass 4: Pick a randomized selection among verified trailing candidates
                if best_candidates:
                    best_gift = random.choice(best_candidates)
                    customer.gift.add(best_gift)
                    assigned_gifts.append(best_gift)
                    assigned_categories.add(category)

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
                    region=region, gift=gift, date_of_purchase=today_date
                ).count()

            max_gifts_per_region = 5  # configurable
            if region_counts.get(region, 0) >= max_gifts_per_region:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
            todays_gift_count = (
                Customer.objects
                .filter(date_of_purchase=today_date, gift__in=offer.gift.all())
                .distinct()
                .count()
            )

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
