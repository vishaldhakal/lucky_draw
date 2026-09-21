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
        import random

        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        # Ensure date_of_purchase is recorded on the customer
        if not customer.date_of_purchase:
            customer.date_of_purchase = today_date
            customer.save(update_fields=["date_of_purchase"])

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

        # Step 1: collect matching offers (EXCLUDING Better Luck Next Time from main evaluation)
        matching_offers = [
            offer
            for offer in electronic_offers
            if self.check_offer_condition(offer, sales_count, customer.region)
            and self.check_validto_condition(offer, phone_model)
        ]

        # Step 2 & 3: group offers by condition value
        offers_by_condition = {}
        for offer in matching_offers:
            try:
                cv = int(offer.offer_condition_value)
            except (ValueError, TypeError):
                cv = 0
            offers_by_condition.setdefault(cv, []).append(offer)

        assigned_gifts = []
        assigned_categories = set()

        # Step 4: assign gifts in ASCENDING order (cv = 1 [Minor] FIRST, then cv = 3, 6 [Major])
        for cv in sorted(offers_by_condition.keys()):
            offers = offers_by_condition[cv]

            # Group gifts by category (Minor Gift, Major Gift, etc.)
            offers_by_category = {}
            for offer in offers:
                for gift in offer.gift.all():
                    # DO NOT let "Better Luck Next Time" occupy the Major Gift slot during cv=1
                    if "better luck" in gift.name.lower():
                        continue

                    offers_by_category.setdefault(gift.category, []).append((
                        offer,
                        gift,
                    ))

            # Assign best gift per category
            for category, gift_options in offers_by_category.items():
                if category in assigned_categories:
                    continue

                valid_options = []
                for offer, gift in gift_options:
                    already_assigned = Customer.objects.filter(
                        date_of_purchase=today_date, gift=gift
                    ).count()

                    total_quantity = max(offer.daily_quantity, 1)

                    if already_assigned >= total_quantity:
                        continue

                    assigned_ratio = already_assigned / total_quantity
                    valid_options.append((gift, assigned_ratio))

                if not valid_options:
                    continue

                # Pick least assigned gift for balanced distribution
                lowest_ratio = min(item[1] for item in valid_options)
                tolerance = 0.01

                best_candidates = [
                    gift
                    for gift, ratio in valid_options
                    if ratio <= (lowest_ratio + tolerance)
                ]

                if best_candidates:
                    selected_gift = random.choice(best_candidates)
                    customer.gift.add(selected_gift)
                    assigned_gifts.append(selected_gift)
                    assigned_categories.add(category)  # Mark category as assigned

        # Step 5: Save prize details or assign fallback
        if assigned_gifts:
            gift_names = ", ".join([gift.name for gift in assigned_gifts])
            customer.prize_details = f"Congratulations! You've won {gift_names}"
            customer.save()
        else:
            self._assign_fallback(customer, lucky_draw_system)

    def _assign_fallback(self, customer, lucky_draw_system):
        """Helper method to assign 'Better Luck Next Time' when no gifts are won"""
        better_luck_gift = GiftItem.objects.filter(
            lucky_draw_system=lucky_draw_system, name__icontains="better luck next time"
        ).first()

        if better_luck_gift:
            customer.gift.set([better_luck_gift])
            customer.prize_details = "Better luck next time!"
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

            max_gifts_per_region = 5
            if region_counts.get(region, 0) >= max_gifts_per_region:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
            # Calculate todays_gift_count for specific items in this offer
            todays_gift_count = (
                Customer.objects
                .filter(date_of_purchase=today_date, gift__in=offer.gift.all())
                .distinct()
                .count()
            )

            try:
                cond_val = int(offer.offer_condition_value)
            except (ValueError, TypeError):
                cond_val = 1

            is_modulo_match = (sales_count % cond_val == 0) if cond_val > 0 else False

            return is_modulo_match and todays_gift_count < offer.daily_quantity

        elif offer.type_of_offer == "At certain sale position":
            sale_nums = offer.sale_numbers or []
            return (
                (str(sales_count) in sale_nums)
                or (sales_count in sale_nums)
                or (str(sales_count) in [str(x) for x in sale_nums])
            )

        return False

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True

        for condition in offer.valid_condition.all():
            if phone_model and phone_model.startswith(condition.condition):
                return True

        return False
