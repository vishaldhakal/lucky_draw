import csv
import datetime
import io

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    IMEINO,
    Customer,
    ElectronicOfferCondition,
    ElectronicsShopOffer,
    FixOffer,
    GiftItem,
    LuckyDrawSystem,
    MobileOfferCondition,
    MobilePhoneOffer,
    RechargeCard,
    RechargeCardOffer,
    Sales,
)
from .serializers import (
    CustomerGiftSerializer,
    CustomerSerializer,
    ElectronicShopOfferConditionSerializer,
    ElectronicsShopOfferSerializer,
    FixOfferSerializer,
    GetOrganiazationDetail,
    GiftItemSerializer,
    IMEINOSerializer,
    LuckyDrawSystemSerializer,
    MobileOfferConditionSerializer,
    MobilePhoneOfferSerializer,
    RechargeCardOfferSerializer,
    RechargeCardSerializer,
)


# Create your views here.
class GetOrganizationDetails(generics.GenericAPIView):
    serializer_class = GetOrganiazationDetail

    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        try:
            organization = LuckyDrawSystem.objects.get(organization__id=organization_id)
            serializer = self.get_serializer(organization)
            return Response(serializer.data)
        except LuckyDrawSystem.DoesNotExist:
            return Response(
                {"error": f"Organization with name '{organization_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class LuckyDrawSystemListCreateView(generics.ListCreateAPIView):
    serializer_class = LuckyDrawSystemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LuckyDrawSystem.objects.filter(
            organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        organization = request.data.get("organization")
        name = request.data.get("name")
        description = request.data.get("description")
        background_image = request.data.get("background_image")
        hero_image = request.data.get("hero_image")
        main_offer_stamp_image = request.data.get("main_offer_stamp_image")
        qr = request.data.get("qr")
        type = request.data.get("type")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        how_to_participate = request.data.get("how_to_participate")
        redeem_condition = request.data.get("redeem_condition")
        terms_and_conditions = request.data.get("terms_and_conditions")

        lucky_draw_system = LuckyDrawSystem.objects.create(
            organization=organization,
            name=name,
            description=description,
            background_image=background_image,
            hero_image=hero_image,
            main_offer_stamp_image=main_offer_stamp_image,
            qr=qr,
            type=type,
            start_date=start_date,
            end_date=end_date,
            how_to_participate=how_to_participate,
            redeem_condition=redeem_condition,
            terms_and_conditions=terms_and_conditions,
        )

        lucky_draw_system.save()
        serializer = LuckyDrawSystemSerializer(lucky_draw_system)
        return Response(serializer.data)


class LuckyDrawSystemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LuckyDrawSystemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LuckyDrawSystem.objects.filter(
            organization=self.request.user.organization
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        name = request.data.get("name")
        description = request.data.get("description")
        background_image = request.data.get("background_image")
        hero_image = request.data.get("hero_image")
        main_offer_stamp_image = request.data.get("main_offer_stamp_image")
        qr = request.data.get("qr")
        type = request.data.get("type")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        how_to_participate = request.data.get("how_to_participate")
        redeem_condition = request.data.get("redeem_condition")
        terms_and_conditions = request.data.get("terms_and_conditions")

        # Update the instance fields if provided in the request
        if name is not None:
            instance.name = name
        if description is not None:
            instance.description = description
        if background_image is not None:
            instance.background_image = background_image
        if hero_image is not None:
            instance.hero_image = hero_image
        if main_offer_stamp_image is not None:
            instance.main_offer_stamp_image = main_offer_stamp_image
        if qr is not None:
            instance.qr = qr
        if type is not None:
            instance.type = type
        if start_date is not None:
            instance.start_date = start_date
        if end_date is not None:
            instance.end_date = end_date
        if how_to_participate is not None:
            instance.how_to_participate = how_to_participate
        if redeem_condition is not None:
            instance.redeem_condition = redeem_condition
        if terms_and_conditions is not None:
            instance.terms_and_conditions = terms_and_conditions

        # Save the updated instance
        instance.save()

        # Serialize and return the updated instance
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GiftItemListCreateView(generics.ListCreateAPIView):
    serializer_class = GiftItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system_id = self.request.GET["lucky_draw_system_id"]
        return GiftItem.objects.filter(lucky_draw_system__id=lucky_draw_system_id)

    def create(self, request):
        lucky_draw_system_id = self.request.GET["lucky_draw_system_id"]
        name = request.data.get("name")
        image = request.data.get("image")

        gift_item = GiftItem.objects.create(
            lucky_draw_system_id=lucky_draw_system_id, name=name, image=image
        )

        gift_item.save()
        gift_item_uploaded = GiftItem.objects.get(id=gift_item.id)
        serializer = GiftItemSerializer(gift_item_uploaded)
        data = serializer.data
        data["image"] = request.build_absolute_uri(data["image"])
        return Response(data)


class GiftItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GiftItem.objects.all()
    serializer_class = GiftItemSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Get the data from the request
        name = request.data.get("name")
        image = request.data.get("image")
        lucky_draw_system = request.data.get("lucky_draw_system")

        # Update the instance fields if provided in the request
        if name is not None:
            instance.name = name
        if image is not None:
            instance.image = image
        if lucky_draw_system is not None:
            instance.lucky_draw_system_id = lucky_draw_system

        # Save the updated instance
        instance.save()

        # Serialize and return the updated instance
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class RechargeCardListCreateView(generics.ListCreateAPIView):
    serializer_class = RechargeCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RechargeCard.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        cardno = request.data.get("cardno")
        provider = request.data.get("provider")
        amount = request.data.get("amount")
        is_assigned = request.data.get("is_assigned")

        recharge_card = RechargeCard.objects.create(
            lucky_draw_system=lucky_draw_system,
            cardno=cardno,
            provider=provider,
            amount=amount,
            is_assigned=is_assigned,
        )
        recharge_card.save()
        serializer = RechargeCardSerializer(recharge_card)
        return Response(serializer.data)


class RechargeCardRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RechargeCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RechargeCard.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        lucky_draw_system = request.data.get("lucky_draw_system")
        cardno = request.data.get("cardno")
        provider = request.data.get("provider")
        amount = request.data.get("amount")
        is_assigned = request.data.get("is_assigned")

        if lucky_draw_system is not None:
            instance.lucky_draw_system_id = lucky_draw_system
        if cardno is not None:
            instance.cardno = cardno
        if provider is not None:
            instance.provider = provider
        if amount is not None:
            instance.amount = amount
        if is_assigned is not None:
            instance.is_assigned = is_assigned

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IMEINOListCreateView(generics.ListCreateAPIView):
    serializer_class = IMEINOSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IMEINO.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        phone_model = request.data.get("phone_model")
        lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)

        imeino = IMEINO.objects.create(
            lucky_draw_system=lucky_draw, imei_no=imei_no, phone_model=phone_model
        )
        imeino.save()
        serializer = IMEINOSerializer(imeino)
        return Response(serializer.data)


class IMEINORetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IMEINOSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IMEINO.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        lucky_draw_system = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        phone_model = request.data.get("phone_model")

        if lucky_draw_system is not None:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
            instance.lucky_draw_system = lucky_draw
        if imei_no is not None:
            instance.imei_no = imei_no
        if phone_model is not None:
            instance.phone_model = phone_model

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FixOfferListCreateView(generics.ListCreateAPIView):
    serializer_class = FixOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FixOffer.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system_id = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        quantity = request.data.get("quantity")
        gift_ids = request.data.get("gift", [])

        lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)

        fix_offer = FixOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            imei_no=imei_no,
            quantity=quantity,
        )
        if gift_ids:
            fix_offer.gift.set(gift_ids)
        fix_offer.save()
        serializer = FixOfferSerializer(fix_offer)
        return Response(serializer.data)


class FixOfferRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FixOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FixOffer.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        lucky_draw_system_id = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        quantity = request.data.get("quantity")
        gift_ids = request.data.get("gift", [])

        if lucky_draw_system_id is not None:
            instance.lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)
        if imei_no is not None:
            instance.imei_no = imei_no
        if quantity is not None:
            instance.quantity = quantity
        if gift_ids is not None:
            instance.gift.set(gift_ids)

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MobileOfferConditionListCreateView(generics.ListCreateAPIView):
    serializer_class = MobileOfferConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MobileOfferCondition.objects.all()

    def create(self, request, *args, **kwargs):
        offer_condition_name = request.data.get("offer_condition_name")
        condition = request.data.get("condition")

        mobile_type = MobileOfferCondition.objects.create(
            offer_type_name=offer_condition_name, condition=condition
        )
        mobile_type.save()
        serializer = MobileOfferConditionSerializer(mobile_type)
        return Response(serializer.data)


class MobileOfferConditionRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = MobileOfferCondition.objects.all()
    serializer_class = MobileOfferConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MobileOfferCondition.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        offer_type_name = request.data.get("offer_type_name", instance.offer_type_name)
        condition = request.data.get("condition", instance.condition)

        instance.offer_type_name = offer_type_name
        instance.condition = condition
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Mobile offer condition deleted successfully"})


class MobilePhoneOfferListCreateView(generics.ListCreateAPIView):
    serializer_class = MobilePhoneOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system_id = self.request.GET["lucky_draw_system_id"]
        return MobilePhoneOffer.objects.filter(
            lucky_draw_system__id=lucky_draw_system_id
        )

    def create(self, request, *args, **kwargs):
        data = request.data
        lucky_draw_system_id = data.get("lucky_draw_system")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        daily_quantity = data.get("daily_quantity")
        type_of_offer = data.get("type_of_offer")
        offer_condition_value = data.get("offer_condition_value")
        sale_numbers = data.get("sale_numbers")
        gift_id = data.get("gift")
        priority = data.get("priority")

        lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)
        gift = GiftItem.objects.get(id=gift_id)

        mobile_phone_offer = MobilePhoneOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            start_date=start_date,
            end_date=end_date,
            daily_quantity=daily_quantity,
            type_of_offer=type_of_offer,
            offer_condition_value=offer_condition_value,
            sale_numbers=sale_numbers,
            gift=gift,
            priority=priority,
        )

        valid_conditions = data.get("valid_condition", [])

        for condition in valid_conditions:
            condt = MobileOfferCondition.objects.get(id=condition)
            mobile_phone_offer.valid_condition.add(condt)

        mobile_phone_offer.save()
        serializer = MobilePhoneOfferSerializer(mobile_phone_offer)
        return Response(serializer.data)


class MobilePhoneOfferRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MobilePhoneOffer.objects.all()
    serializer_class = MobilePhoneOfferSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        data = request.data

        start_date = data.get("start_date")
        end_date = data.get("end_date")
        daily_quantity = data.get("daily_quantity")
        type_of_offer = data.get("type_of_offer")
        offer_condition_value = data.get("offer_condition_value")
        sale_numbers = data.get("sale_numbers")
        gift_id = data.get("gift")
        priority = data.get("priority")

        gift = GiftItem.objects.get(id=gift_id)

        instance = self.get_object()

        instance.start_date = start_date
        instance.end_date = end_date
        instance.daily_quantity = daily_quantity
        instance.type_of_offer = type_of_offer
        instance.offer_condition_value = offer_condition_value
        instance.sale_numbers = sale_numbers
        instance.gift = gift
        instance.priority = priority

        valid_conditions = data.get("valid_condition", [])
        instance.valid_condition.clear()
        for condition in valid_conditions:
            condt = MobileOfferCondition.objects.get(id=condition)
            instance.valid_condition.add(condt)

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Mobile phone offer deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class RechargeCardOfferListCreateView(generics.ListCreateAPIView):
    serializer_class = RechargeCardOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RechargeCardOffer.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        daily_quantity = request.data.get("daily_quantity")
        type_of_offer = request.data.get("type_of_offer")
        offer_condition_value = request.data.get("offer_condition_value")
        sale_numbers = request.data.get("sale_numbers")

        amount = request.data.get("amount")
        provider = request.data.get("provider")

        recharge_card_offer = RechargeCardOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            start_date=start_date,
            end_date=end_date,
            daily_quantity=daily_quantity,
            type_of_offer=type_of_offer,
            offer_condition_value=offer_condition_value,
            sale_numbers=sale_numbers,
            amount=amount,
            provider=provider,
        )
        valid_conditions = request.data.get("valid_condition", [])
        recharge_card_offer.valid_condition.set(valid_conditions)

        recharge_card_offer.save()
        serializer = RechargeCardOfferSerializer(recharge_card_offer)
        return Response(serializer.data)


class RechargeCardOfferRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RechargeCardOffer.objects.all()
    serializer_class = RechargeCardOfferSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Get updated data or default to existing values
        instance.lucky_draw_system = request.data.get(
            "lucky_draw_system", instance.lucky_draw_system
        )
        instance.start_date = request.data.get("start_date", instance.start_date)
        instance.end_date = request.data.get("end_date", instance.end_date)
        instance.daily_quantity = request.data.get(
            "daily_quantity", instance.daily_quantity
        )
        instance.type_of_offer = request.data.get(
            "type_of_offer", instance.type_of_offer
        )
        instance.offer_condition_value = request.data.get(
            "offer_condition_value", instance.offer_condition_value
        )
        instance.sale_numbers = request.data.get("sale_numbers", instance.sale_numbers)
        instance.amount = request.data.get("amount", instance.amount)
        instance.provider = request.data.get("provider", instance.provider)

        # Handling many-to-many field (valid_condition)
        valid_conditions = request.data.get("valid_condition", [])
        if valid_conditions:
            instance.valid_condition.set(valid_conditions)

        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Recharge card offer deleted successfully"})


class ElectronicOfferConditionListCreateView(generics.ListCreateAPIView):
    serializer_class = ElectronicShopOfferConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ElectronicOfferCondition.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        offer_condition_name = request.data.get("offer_condition_name")
        condition = request.data.get("condition")

        electronic_offer_condition = ElectronicOfferCondition.objects.create(
            offer_condition_name=offer_condition_name, condition=condition
        )
        electronic_offer_condition.save()

        serializer = self.get_serializer(electronic_offer_condition)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ElectronicOfferConditionRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = ElectronicOfferCondition.objects.all()
    serializer_class = ElectronicShopOfferConditionSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        offer_condition_name = request.data.get(
            "offer_condition_name", instance.offer_condition_name
        )
        condition = request.data.get("condition", instance.condition)

        instance.offer_condition_name = offer_condition_name
        instance.condition = condition
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Electronic offer condition deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class ElectronicsShopOfferListCreateView(generics.ListCreateAPIView):
    serializer_class = ElectronicsShopOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ElectronicsShopOffer.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system_id = request.data.get("lucky_draw_system")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        daily_quantity = request.data.get("daily_quantity")
        type_of_offer = request.data.get("type_of_offer")
        offer_condition_value = request.data.get("offer_condition_value")
        sale_numbers = request.data.get("sale_numbers")
        gifts = request.data.get("gift", [])

        lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)

        electronics_shop_offer = ElectronicsShopOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            start_date=start_date,
            end_date=end_date,
            daily_quantity=daily_quantity,
            type_of_offer=type_of_offer,
            offer_condition_value=offer_condition_value,
            sale_numbers=sale_numbers,
        )

        electronics_shop_offer.gift.set(gifts)

        # Handle many-to-many relationship for valid_condition
        valid_conditions = request.data.get("valid_condition", [])
        electronics_shop_offer.valid_condition.set(valid_conditions)

        electronics_shop_offer.save()

        serializer = self.get_serializer(electronics_shop_offer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ElectronicsShopOfferRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = ElectronicsShopOffer.objects.all()
    serializer_class = ElectronicsShopOfferSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Updating the instance fields with provided data or using existing values
        lucky_draw_system_id = request.data.get(
            "lucky_draw_system", instance.lucky_draw_system.id
        )
        instance.lucky_draw_system = LuckyDrawSystem.objects.get(
            id=lucky_draw_system_id
        )

        instance.start_date = request.data.get("start_date", instance.start_date)
        instance.end_date = request.data.get("end_date", instance.end_date)
        instance.daily_quantity = request.data.get(
            "daily_quantity", instance.daily_quantity
        )
        instance.type_of_offer = request.data.get(
            "type_of_offer", instance.type_of_offer
        )
        instance.offer_condition_value = request.data.get(
            "offer_condition_value", instance.offer_condition_value
        )
        instance.sale_numbers = request.data.get("sale_numbers", instance.sale_numbers)

        # Handling many-to-many relationship for valid_condition
        valid_conditions = request.data.get("valid_condition", [])
        if valid_conditions:
            instance.valid_condition.set(valid_conditions)

        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Electronics shop offer deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class CustomerListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        customer_name = request.data.get("customer_name")
        shop_name = request.data.get("shop_name")
        sold_area = request.data.get("sold_area")
        phone_number = request.data.get("phone_number")
        email = request.data.get("email")
        region = request.data.get("region")

        imei = request.data.get("imei")

        if not imei:
            return Response(
                {"error": "IMEI is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        print(imei)
        try:
            imei_obj = IMEINO.objects.get(imei_no=imei, used=False)
        except IMEINO.DoesNotExist:
            return Response(
                {"error": "Invalid IMEI or IMEI already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imeii = IMEINO.objects.get(imei_no=imei)
        phone_model = imeii.phone_model

        if Customer.objects.filter(imei=imei).exists():
            return Response(
                {"error": "A customer with this IMEI already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        how_know_about_campaign = request.data.get("how_know_about_campaign")
        profession = request.data.get("profession")

        imei_obj.used = True
        imei_obj.save()

        lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)

        customer = Customer.objects.create(
            lucky_draw_system=lucky_draw,
            customer_name=customer_name,
            shop_name=shop_name,
            sold_area=sold_area,
            phone_number=phone_number,
            email=email,
            phone_model=phone_model,
            imei=imei,
            how_know_about_campaign=how_know_about_campaign,
            profession=profession,
        )

        if region:
            customer.region = region

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

        # Fixed Offers
        fixed_offer = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw_system, imei_no=customer.imei, quantity__gt=0
        ).first()

        if fixed_offer:
            selected_gift = fixed_offer.gift.first()
            if selected_gift:
                customer.gift.set([selected_gift])
                customer.prize_details = (
                    f"Congratulations! You've won {selected_gift.name}"
                )
                customer.save()
                fixed_offer.quantity -= 1
                fixed_offer.save()
                return

        mobile_offers = MobilePhoneOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            start_date__lte=today_date,
            end_date__gte=today_date,
            daily_quantity__gt=0,
        ).order_by("priority")

        for offer in mobile_offers:
            if customer.region != "None":
                condition_met = self.check_offer_condition(
                    offer, sales_count, customer.region
                )
            else:
                condition_met = self.check_offer_condition(offer, sales_count, "Other")
            validto_check = self.check_validto_condition(offer, phone_model)

            if condition_met and validto_check:
                # Customer.gift is ManyToMany; assign single FK gift
                customer.gift.set([offer.gift])
                customer.prize_details = (
                    f"Congratulations! You've won {offer.gift.name}"
                )

                customer.save()
                offer.save()
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
                # ElectronicsShopOffer.gift is a ManyToMany; pick a single gift to assign
                selected_gift = None
                try:
                    # If M2M manager
                    selected_gift = offer.gift.first()
                except Exception:
                    # If it's already a FK, use as is
                    selected_gift = getattr(offer, "gift", None)

                if not selected_gift:
                    # No gift available to assign; skip to next offer
                    continue

                # Customer.gift is ManyToMany; assign the selected gift
                customer.gift.set([selected_gift])
                customer.prize_details = f"Congratulations! You've won {selected_gift.name} from our Electronics Shop Offer!"
                customer.save()

                offer.save()
                return

        # If no gift assigned
        customer.prize_details = "Thank you for your purchase!"
        customer.save()

    def check_offer_condition(self, offer, sales_count, region):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        # Handle both FK and M2M gift relationships gracefully
        selected_gift = None
        try:
            # If gift is a ManyToMany manager
            if hasattr(offer, "gift") and hasattr(offer.gift, "all"):
                selected_gift = offer.gift.first()
            else:
                selected_gift = getattr(offer, "gift", None)
        except Exception:
            selected_gift = getattr(offer, "gift", None)

        if offer.has_region_limit:
            if region == "None" or region == "Other":
                return False

            if not selected_gift:
                # If we cannot determine a concrete gift, conservatively disallow the region-limited offer
                return False

            region_counts = {
                "Centeral Region": Customer.objects.filter(
                    region="Centeral Region", gift=selected_gift
                ).count(),
                "Eastern Region": Customer.objects.filter(
                    region="Eastern Region", gift=selected_gift
                ).count(),
                "Western Region": Customer.objects.filter(
                    region="Western Region", gift=selected_gift
                ).count(),
            }

            min_count = min(region_counts.values())

            if region_counts[region] > min_count:
                return False

        if offer.has_time_limit:
            if today_time < offer.start_time or today_time > offer.end_time:
                return False

        if offer.type_of_offer == "After every certain sale":
            todayscount = 0
            if selected_gift:
                todayscount = Customer.objects.filter(
                    date_of_purchase=today_date, gift=selected_gift
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


@api_view(["GET"])
def GetGiftList(request):
    lucky_draw_system_id = request.GET["lucky_draw_system_id"]
    lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)
    gifts = GiftItem.objects.filter(lucky_draw_system=lucky_draw_system)
    serializer = GiftItemSerializer(gifts, many=True)
    data = serializer.data
    # data["image"] = request.build_absolute_uri(data["image"])
    for gift in data:
        gift["image"] = request.build_absolute_uri(gift["image"])
    return Response(data)


@api_view(["GET"])
def gift_count_last_100(request):
    """
    Returns the number of each gift assigned to customers in the last 100 orders
    for a given lucky draw system.

    Query Params:
    - lucky_draw_system_id: int (required)

    Response format:
    {
      "results": [
        {"gift_id": 1, "gift_name": "Gift A", "count": 10},
        {"gift_id": 2, "gift_name": "Gift B", "count": 5}
      ],
      "total_customers_considered": 100
    }
    """
    lucky_draw_system_id = request.query_params.get("lucky_draw_system_id")
    if not lucky_draw_system_id:
        return Response(
            {"error": "'lucky_draw_system_id' is required as a query parameter."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        lds = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)
    except LuckyDrawSystem.DoesNotExist:
        return Response(
            {"error": "LuckyDrawSystem not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get last 100 customers (orders) for the lucky draw system
    last_ids = list(
        Customer.objects.filter(lucky_draw_system=lds)
        .order_by("-id")
        .values_list("id", flat=True)[:100]
    )

    # Aggregate counts of gifts from those customers via the M2M relation
    # Exclude customers without any assigned gift
    gift_counts = (
        Customer.objects.filter(id__in=last_ids, gift__isnull=False)
        .values("gift__id", "gift__name")
        .annotate(count=Count("gift"))
        .order_by("-count", "gift__name")
    )

    results = [
        {
            "gift_id": row["gift__id"],
            "gift_name": row["gift__name"],
            "count": row["count"],
        }
        for row in gift_counts
    ]

    return Response(
        {
            "results": results,
            "total_customers_considered": len(last_ids),
        }
    )


@api_view(["POST"])
def UploadImeiBulk(request):
    if request.method == "POST":
        file = request.FILES["file"]
        lucky_draw_system_id = request.data.get("lucky_draw_system")
        lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)

        if file.name.endswith(".csv"):
            data_set = file.read().decode("UTF-8")
            io_string = io.StringIO(data_set)
            next(io_string)
            for column in csv.reader(io_string, delimiter=",", quotechar="|"):
                if not IMEINO.objects.filter(imei_no=column[0]).exists():
                    imei = IMEINO()
                    imei.imei_no = column[0]
                    imei.lucky_draw_system = lucky_draw_system
                    imei.phone_model = column[1]
                    imei.save()
            return Response(
                {"message": "IMEI numbers uploaded successfully"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "Invalid file format. Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return Response(
        {"error": "Invalid request method. Please use POST method."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def download_customers_detail(request):
    if request.method == "POST":
        data = request.data
        start_date = data.get("start_date", datetime.date.today())
        end_date = data.get("end_date", datetime.date.today())
        luckydraw = data.get("lucky_draw_system_id", None)

        # Create a base queryset for customers with gifts
        queryset = Customer.objects.all()

        if luckydraw is not None:
            system = LuckyDrawSystem.objects.get(id=luckydraw)
            queryset = queryset.filter(lucky_draw_system=system)

        if start_date and end_date:
            queryset = queryset.filter(date_of_purchase__range=(start_date, end_date))

        if start_date and not end_date:
            queryset = queryset.filter(date_of_purchase=start_date)

        if end_date and not start_date:
            queryset = queryset.filter(date_of_purchase=end_date)

        # Create a CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="customers_detail.csv"'

        # Create a CSV writer and write the header row
        writer = csv.writer(response)
        writer.writerow(
            [
                "Customer Name",
                "Shop Name",
                "Sold Area",
                "Region",
                "Phone Number",
                "Phone Model",
                "Sale Status",
                "Prize Details",
                "IMEI",
                "Gift",
                "Date of Purchase",
                "How Know About Campaign",
                "Profession",
            ]
        )

        # Write the data rows
        for customer in queryset:
            writer.writerow(
                [
                    customer.customer_name,
                    customer.shop_name,
                    customer.sold_area,
                    customer.region,
                    customer.phone_number,
                    customer.phone_model,
                    customer.sale_status,
                    customer.prize_details,
                    customer.imei,
                    ", ".join([gift.name for gift in customer.gift.all()])
                    if customer.gift.exists()
                    else "",
                    customer.date_of_purchase,
                    customer.how_know_about_campaign,
                    customer.profession,
                ]
            )

        return response


def export_data(request, pk):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="today.csv"'
    writer = csv.writer(response)
    luckydraw = LuckyDrawSystem.objects.get(id=pk)
    cust = Customer.objects.filter(lucky_draw_system=luckydraw)

    writer.writerow(
        [
            "Customer Name",
            "Shop Name",
            "Sold Area",
            "Phone Number",
            "Email",
            "Phone Model",
            "IMEI",
            "How Know About Campaign",
            "Profession",
            "Region",
            "Gift",
            "Date of Purchase",
            "Prize Details",
            "Recharge Card",
            "NTC Recharge Card",
            "Amount of Ntc Card",
        ]
    )
    for customer in cust:
        writer.writerow(
            [
                customer.customer_name,
                customer.shop_name,
                customer.sold_area,
                customer.phone_number,
                customer.email,
                customer.phone_model,
                customer.imei,
                customer.how_know_about_campaign,
                customer.profession,
                customer.region,
                ", ".join([gift.name for gift in customer.gift.all()])
                if customer.gift.exists()
                else "",
                customer.date_of_purchase,
                customer.prize_details,
                customer.recharge_card,
                customer.ntc_recharge_card,
                customer.amount_of_card,
            ]
        )
    return response
