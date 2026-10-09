import csv
import datetime

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import generics, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    BulkDeleteLuckyDrawIMEISerializer,
    BulkUploadIMEISerializer,
    BulkUploadIMEIWithRegionSerializer,
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
    UploadFixOfferFileSerializer,
)
from .services import (
    bulk_create_fix_offers_from_file,
    bulk_upload_imeis_from_csv,
    bulk_upload_imeis_with_region_from_file,
    delete_imeis_for_lucky_draw_system,
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
        ).select_related("lucky_draw_system")

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        phone_model = request.data.get("phone_model")
        region = request.data.get("region")
        lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)

        imeino = IMEINO.objects.create(
            lucky_draw_system=lucky_draw,
            imei_no=imei_no,
            phone_model=phone_model,
            region=region,
        )
        imeino.save()
        serializer = IMEINOSerializer(imeino)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IMEINORetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IMEINOSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IMEINO.objects.filter(
            lucky_draw_system__organization=self.request.user.organization
        ).select_related("lucky_draw_system")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        lucky_draw_system = request.data.get("lucky_draw_system")
        imei_no = request.data.get("imei_no")
        phone_model = request.data.get("phone_model")
        region = request.data.get("region")

        if lucky_draw_system is not None:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
            instance.lucky_draw_system = lucky_draw
        if imei_no is not None:
            instance.imei_no = imei_no
        if phone_model is not None:
            instance.phone_model = phone_model
        if region is not None:
            instance.region = region

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteLuckyDrawIMEIsView(generics.GenericAPIView):
    """
    API endpoint to bulk delete all (or unused) IMEI numbers of a selected Lucky Draw System.
    Handles high volumes (40,000+ records) efficiently using chunked batch deletion.
    """

    serializer_class = BulkDeleteLuckyDrawIMEISerializer
    # permission_classes = [IsAuthenticated]

    def _process_bulk_delete(self, request, lucky_draw_system_id=None):
        payload = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )

        # Support lucky_draw_system_id from URL kwarg, request body, or query params
        if lucky_draw_system_id is not None:
            payload["lucky_draw_system"] = lucky_draw_system_id
        elif "lucky_draw_system" not in payload and "lucky_draw_system_id" in payload:
            payload["lucky_draw_system"] = payload.get("lucky_draw_system_id")
        elif "lucky_draw_system" not in payload and request.query_params.get(
            "lucky_draw_system_id"
        ):
            payload["lucky_draw_system"] = request.query_params.get(
                "lucky_draw_system_id"
            )

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        lucky_draw = validated_data["lucky_draw_system"]

        result = delete_imeis_for_lucky_draw_system(
            lucky_draw_system_id=lucky_draw.id,
            only_unused=validated_data.get("only_unused", False),
            batch_size=validated_data.get("batch_size", 5000),
        )

        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, lucky_draw_system_id=None, *args, **kwargs):
        return self._process_bulk_delete(
            request, lucky_draw_system_id=lucky_draw_system_id
        )

    def post(self, request, lucky_draw_system_id=None, *args, **kwargs):
        return self._process_bulk_delete(
            request, lucky_draw_system_id=lucky_draw_system_id
        )


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
            instance.lucky_draw_system = LuckyDrawSystem.objects.get(
                id=lucky_draw_system_id
            )
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


class UploadFixOfferBulkView(generics.GenericAPIView):
    """
    API endpoint to bulk upload IMEI numbers from a CSV or Excel (.xlsx, .xls) file,
    select a gift, and create/update FixOffer records for that Lucky Draw System.
    """

    serializer_class = UploadFixOfferFileSerializer
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        payload = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        if "file" not in payload and "file" in request.FILES:
            payload["file"] = request.FILES["file"]

        serializer = self.get_serializer(data=payload)
        if not serializer.is_valid():
            first_field = next(iter(serializer.errors))
            first_err = serializer.errors[first_field]
            err_msg = (
                first_err[0]
                if isinstance(first_err, list) and first_err
                else str(first_err)
            )
            return Response(
                {"error": err_msg, "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        lucky_draw_system = validated_data["lucky_draw_system"]
        selected_gifts = validated_data["selected_gifts"]
        file_obj = validated_data["file"]
        quantity = validated_data.get("quantity", 1)
        replace_existing = validated_data.get("replace_existing", True)
        batch_size = validated_data.get("batch_size", 2000)

        org = None
        if (
            hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            and hasattr(request.user, "organization")
            and request.user.organization
            and not getattr(request.user, "is_superuser", False)
        ):
            org = request.user.organization

        try:
            result = bulk_create_fix_offers_from_file(
                lucky_draw_system_id=lucky_draw_system.id,
                file_obj=file_obj,
                gift_ids=[g.id for g in selected_gifts],
                quantity=quantity,
                organization=org,
                replace_existing=replace_existing,
                batch_size=batch_size,
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            err_msg = (
                e.message
                if hasattr(e, "message")
                else (
                    e.messages[0] if hasattr(e, "messages") and e.messages else str(e)
                )
            )
            return Response(
                {"error": err_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to upload fix offers: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
        has_region_limit = data.get("has_region_limit", False)
        target_regions = data.get("target_regions")

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
            has_region_limit=has_region_limit,
            target_regions=target_regions,
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

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Customer.objects.select_related("lucky_draw_system").filter(
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

        if not lucky_draw_system:
            return Response(
                {"error": "Lucky draw system is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
        except (LuckyDrawSystem.DoesNotExist, ValueError):
            return Response(
                {"error": "Invalid Lucky Draw System."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if lucky_draw.end_date < timezone.now().date():
            return Response(
                {"error": "Lucky draw campaign has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imei = request.data.get("imei")

        if not imei:
            return Response(
                {"error": "IMEI is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            imei_obj = IMEINO.objects.get(
                imei_no=imei, lucky_draw_system=lucky_draw, used=False
            )
        except IMEINO.DoesNotExist:
            return Response(
                {"error": "Invalid IMEI or IMEI already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_model = imei_obj.phone_model

        if Customer.objects.filter(imei=imei).exists():
            return Response(
                {"error": "A customer with this IMEI already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        how_know_about_campaign = request.data.get("how_know_about_campaign")
        profession = request.data.get("profession")

        imei_obj.used = True
        imei_obj.save()

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
        import random

        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        sales_today, _ = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )
        sales_today.sales_count += 1
        sales_today.save()
        sales_count = sales_today.sales_count

        phone_model = customer.phone_model

        # 1. FIXED OFFERS
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

        # 2. FETCH ACTIVE OFFERS
        mobile_offers = list(
            MobilePhoneOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        electronic_offers = list(
            ElectronicsShopOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        region_str = (
            customer.region
            if (customer.region and customer.region != "None")
            else "Other"
        )

        matching_offers = []

        for offer in mobile_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                matching_offers.append(offer)

        for offer in electronic_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                matching_offers.append(offer)

        if matching_offers:
            selected_gift = None

            # CHECK IF ANY MATCHED OFFER HAS AN EXPLICIT PRIORITY (> 0)
            has_explicit_priority = any(
                getattr(o, "priority", 0) > 0 for o in matching_offers
            )

            if has_explicit_priority:
                # ROUTE A: PRIORITY 1 FIRST
                # Filter out offers with priority 0, then sort ASCENDING (1 -> 2 -> 3...)
                priority_offers = [
                    o for o in matching_offers if getattr(o, "priority", 0) > 0
                ]
                sorted_offers = sorted(
                    priority_offers, key=lambda x: getattr(x, "priority")
                )

                for offer in sorted_offers:
                    gifts = (
                        list(offer.gift.all())
                        if hasattr(offer.gift, "all")
                        else [getattr(offer, "gift", None)]
                    )

                    valid_options = []
                    for gift in gifts:
                        if not gift:
                            continue

                        already_assigned = Customer.objects.filter(
                            date_of_purchase=today_date, gift=gift
                        ).count()

                        target_capacity = max(offer.daily_quantity, 1)

                        if already_assigned < target_capacity:
                            assigned_ratio = already_assigned / target_capacity
                            valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]
                        selected_gift = random.choice(best_candidates)
                        break  # Stop immediately at Priority 1 (or lowest priority number matched)

            if not selected_gift:
                # ROUTE B: NORMAL EVALUATION (If no explicit priority matched or priority offers out of stock)
                offers_by_cv = {}
                for offer in matching_offers:
                    try:
                        cv = int(offer.offer_condition_value)
                    except (ValueError, TypeError):
                        cv = 1
                    offers_by_cv.setdefault(cv, []).append(offer)

                sorted_cvs = sorted(offers_by_cv.keys(), reverse=True)

                for cv in sorted_cvs:
                    valid_options = []
                    for offer in offers_by_cv[cv]:
                        gifts = (
                            list(offer.gift.all())
                            if hasattr(offer.gift, "all")
                            else [getattr(offer, "gift", None)]
                        )

                        for gift in gifts:
                            if not gift:
                                continue

                            already_assigned = Customer.objects.filter(
                                date_of_purchase=today_date, gift=gift
                            ).count()

                            target_capacity = max(offer.daily_quantity, 1)

                            if already_assigned < target_capacity:
                                assigned_ratio = already_assigned / target_capacity
                                valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]

                        if best_candidates:
                            selected_gift = random.choice(best_candidates)
                            break

            if selected_gift:
                customer.gift.set([selected_gift])
                if (
                    "thank you" in selected_gift.name.lower()
                    or "better luck" in selected_gift.name.lower()
                ):
                    customer.prize_details = "Thank you for your purchase!"
                else:
                    customer.prize_details = (
                        f"Congratulations! You've won {selected_gift.name}"
                    )
                customer.save()
                return

        # 3. FALLBACK FOR UNMATCHED SPINS / EXHAUSTED CAPS
        better_luck_gift = GiftItem.objects.filter(
            lucky_draw_system=lucky_draw_system, name__icontains="thank you"
        ).first()

        if better_luck_gift:
            customer.gift.set([better_luck_gift])
            customer.prize_details = "Thank you for your purchase!"
        else:
            customer.prize_details = "Thank you for your purchase!"

        customer.save()

    def check_offer_condition(self, offer, sales_count, region):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        if hasattr(offer, "gift") and hasattr(offer.gift, "all"):
            selected_gift = offer.gift.first()
        else:
            selected_gift = getattr(offer, "gift", None)

        # 1. Target region exclusivity check
        target_regions_str = getattr(offer, "target_regions", None)
        if target_regions_str:
            allowed_regions = [
                r.strip().lower() for r in target_regions_str.split(",") if r.strip()
            ]
            if (
                not region
                or region in ("None", "Other")
                or region.strip().lower() not in allowed_regions
            ):
                return False

        # 2. Region balancing check
        if offer.has_region_limit:
            if region == "None" or region == "Other":
                return False
            if not selected_gift:
                return False

            region_counts = {
                "Centeral Region": Customer.objects.filter(
                    region="Centeral Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
                "Eastern Region": Customer.objects.filter(
                    region="Eastern Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
                "Western Region": Customer.objects.filter(
                    region="Western Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
            }
            min_count = min(region_counts.values())
            if region_counts.get(region, 0) > min_count:
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

            try:
                cond_val = int(offer.offer_condition_value)
            except (ValueError, TypeError):
                cond_val = 1

            # Cumulative unlocked gifts based on intervals reached so far today.
            # If an earlier interval was reached by an ineligible customer (e.g. from another region),
            # the prize remains unawarded and rolls over to the next eligible customer.
            intervals_reached = (sales_count // cond_val) if cond_val > 0 else 0
            target_capacity = (
                offer.daily_quantity if offer.daily_quantity > 0 else intervals_reached
            )
            max_allowed = min(intervals_reached, target_capacity)

            return todayscount < max_allowed

        elif offer.type_of_offer == "At certain sale position":
            todayscount = 0
            if selected_gift:
                todayscount = Customer.objects.filter(
                    date_of_purchase=today_date, gift=selected_gift
                ).count()

            sale_nums = offer.sale_numbers or []
            parsed_positions = []
            for num in sale_nums:
                try:
                    parsed_positions.append(int(num))
                except (ValueError, TypeError):
                    continue

            # Count how many milestone positions have unlocked at or before the current sales count.
            # If a position hit an ineligible customer, it remains unclaimed until the next eligible customer.
            positions_unlocked = sum(1 for p in parsed_positions if p <= sales_count)
            target_capacity = (
                offer.daily_quantity
                if offer.daily_quantity > 0
                else len(parsed_positions)
            )
            max_allowed = min(positions_unlocked, target_capacity)

            return todayscount < max_allowed

        return False

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True

        if not phone_model:
            return False

        phone_model_str = str(phone_model).strip()
        for condition in offer.valid_condition.all():
            cond_str = str(condition.condition).strip()
            if (
                phone_model_str.lower().startswith(cond_str.lower())
                or cond_str.lower() in phone_model_str.lower()
            ):
                return True

        return False


class InfinixCustomerListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Customer.objects.select_related("lucky_draw_system").filter(
            lucky_draw_system__organization=self.request.user.organization
        )

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get("lucky_draw_system")
        customer_name = request.data.get("customer_name")
        shop_name = request.data.get("shop_name")
        sold_area = request.data.get("sold_area")
        phone_number = request.data.get("phone_number")
        email = request.data.get("email")

        if not lucky_draw_system:
            return Response(
                {"error": "Lucky draw system is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
        except (LuckyDrawSystem.DoesNotExist, ValueError):
            return Response(
                {"error": "Invalid Lucky Draw System."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if lucky_draw.end_date < timezone.now().date():
            return Response(
                {"error": "Lucky draw campaign has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imei = request.data.get("imei")

        if not imei:
            return Response(
                {"error": "IMEI is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            imei_obj = IMEINO.objects.get(
                imei_no=imei, lucky_draw_system=lucky_draw, used=False
            )
        except IMEINO.DoesNotExist:
            return Response(
                {"error": "Invalid IMEI or IMEI already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_model = imei_obj.phone_model

        # Get region directly from IMEI number record
        region = (
            imei_obj.region.strip()
            if imei_obj.region and imei_obj.region.strip() not in ("None", "")
            else request.data.get("region")
        )

        if Customer.objects.filter(imei=imei).exists():
            return Response(
                {"error": "A customer with this IMEI already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        how_know_about_campaign = request.data.get("how_know_about_campaign")
        profession = request.data.get("profession")

        imei_obj.used = True
        imei_obj.save()

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
            region=region if region else "None",
        )

        if region:
            customer.region = region

        self.assign_gift(customer)

        serializer = CustomerGiftSerializer(customer)
        data = serializer.data
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
        import random

        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        sales_today, _ = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )
        sales_today.sales_count += 1
        sales_today.save()
        sales_count = sales_today.sales_count

        phone_model = customer.phone_model

        # 1. FIXED OFFERS
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

        # 2. FETCH ACTIVE OFFERS
        mobile_offers = list(
            MobilePhoneOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        electronic_offers = list(
            ElectronicsShopOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        region_str = (
            customer.region
            if (customer.region and customer.region != "None")
            else "Other"
        )

        matching_offers = []

        for offer in mobile_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                matching_offers.append(offer)

        for offer in electronic_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                matching_offers.append(offer)

        if matching_offers:
            selected_gift = None

            # CHECK IF ANY MATCHED OFFER HAS AN EXPLICIT PRIORITY (> 0)
            has_explicit_priority = any(
                getattr(o, "priority", 0) > 0 for o in matching_offers
            )

            if has_explicit_priority:
                # ROUTE A: PRIORITY 1 FIRST
                # Filter out offers with priority 0, then sort ASCENDING (1 -> 2 -> 3...)
                priority_offers = [
                    o for o in matching_offers if getattr(o, "priority", 0) > 0
                ]
                sorted_offers = sorted(
                    priority_offers, key=lambda x: getattr(x, "priority")
                )

                for offer in sorted_offers:
                    gifts = (
                        list(offer.gift.all())
                        if hasattr(offer.gift, "all")
                        else [getattr(offer, "gift", None)]
                    )

                    valid_options = []
                    for gift in gifts:
                        if not gift:
                            continue

                        already_assigned = Customer.objects.filter(
                            date_of_purchase=today_date, gift=gift
                        ).count()

                        target_capacity = max(offer.daily_quantity, 1)

                        if already_assigned < target_capacity:
                            assigned_ratio = already_assigned / target_capacity
                            valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]
                        selected_gift = random.choice(best_candidates)
                        break  # Stop immediately at Priority 1 (or lowest priority number matched)

            if not selected_gift:
                # ROUTE B: NORMAL EVALUATION (If no explicit priority matched or priority offers out of stock)
                offers_by_cv = {}
                for offer in matching_offers:
                    try:
                        cv = int(offer.offer_condition_value)
                    except (ValueError, TypeError):
                        cv = 1
                    offers_by_cv.setdefault(cv, []).append(offer)

                sorted_cvs = sorted(offers_by_cv.keys(), reverse=True)

                for cv in sorted_cvs:
                    valid_options = []
                    for offer in offers_by_cv[cv]:
                        gifts = (
                            list(offer.gift.all())
                            if hasattr(offer.gift, "all")
                            else [getattr(offer, "gift", None)]
                        )

                        for gift in gifts:
                            if not gift:
                                continue

                            already_assigned = Customer.objects.filter(
                                date_of_purchase=today_date, gift=gift
                            ).count()

                            target_capacity = max(offer.daily_quantity, 1)

                            if already_assigned < target_capacity:
                                assigned_ratio = already_assigned / target_capacity
                                valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]

                        if best_candidates:
                            selected_gift = random.choice(best_candidates)
                            break

            if selected_gift:
                customer.gift.set([selected_gift])
                if (
                    "thank you" in selected_gift.name.lower()
                    or "better luck" in selected_gift.name.lower()
                ):
                    customer.prize_details = "Thank you for your purchase!"
                else:
                    customer.prize_details = (
                        f"Congratulations! You've won {selected_gift.name}"
                    )
                customer.save()
                return

        # 3. FALLBACK FOR UNMATCHED SPINS / EXHAUSTED CAPS
        better_luck_gift = GiftItem.objects.filter(
            lucky_draw_system=lucky_draw_system, name__icontains="thank you"
        ).first()

        if better_luck_gift:
            customer.gift.set([better_luck_gift])
            customer.prize_details = "Thank you for your purchase!"
        else:
            customer.prize_details = "Thank you for your purchase!"

        customer.save()

    def check_offer_condition(self, offer, sales_count, region):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        if hasattr(offer, "gift") and hasattr(offer.gift, "all"):
            selected_gift = offer.gift.first()
        else:
            selected_gift = getattr(offer, "gift", None)

        # 1. Target region exclusivity check
        target_regions_str = getattr(offer, "target_regions", None)
        allowed_regions = []
        if target_regions_str:
            allowed_regions = [
                r.strip().lower() for r in target_regions_str.split(",") if r.strip()
            ]
            if (
                not region
                or region in ("None", "Other")
                or region.strip().lower() not in allowed_regions
            ):
                return False

        # 2. Dynamic region balancing check
        if offer.has_region_limit:
            if not region or region in ("None", "Other"):
                return False
            if not selected_gift:
                return False

            lucky_draw_system = offer.lucky_draw_system

            # Dynamic list of active regions from IMEINO and Customer for this lucky draw system
            imei_regions = set(
                IMEINO.objects
                .filter(lucky_draw_system=lucky_draw_system)
                .exclude(region__isnull=True)
                .exclude(region__in=["", "None", "Other"])
                .values_list("region", flat=True)
                .distinct()
            )
            customer_regions = set(
                Customer.objects
                .filter(lucky_draw_system=lucky_draw_system)
                .exclude(region__isnull=True)
                .exclude(region__in=["", "None", "Other"])
                .values_list("region", flat=True)
                .distinct()
            )
            all_regions = list(imei_regions | customer_regions)

            if allowed_regions:
                all_regions = [
                    r for r in all_regions if r.strip().lower() in allowed_regions
                ]

            if region not in all_regions:
                all_regions.append(region)

            if all_regions:
                daily_counts_qs = (
                    Customer.objects
                    .filter(
                        lucky_draw_system=lucky_draw_system,
                        gift=selected_gift,
                        date_of_purchase=today_date,
                        region__in=all_regions,
                    )
                    .values("region")
                    .annotate(total=Count("id"))
                )
                counts_by_region = {
                    item["region"]: item["total"] for item in daily_counts_qs
                }
                region_counts = {r: counts_by_region.get(r, 0) for r in all_regions}

                min_count = min(region_counts.values())
                if region_counts.get(region, 0) > min_count:
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

            try:
                cond_val = int(offer.offer_condition_value)
            except (ValueError, TypeError):
                cond_val = 1

            # Cumulative unlocked gifts based on intervals reached so far today.
            # If an earlier interval was reached by an ineligible customer (e.g. from another region),
            # the prize remains unawarded and rolls over to the next eligible customer.
            intervals_reached = (sales_count // cond_val) if cond_val > 0 else 0
            target_capacity = (
                offer.daily_quantity if offer.daily_quantity > 0 else intervals_reached
            )
            max_allowed = min(intervals_reached, target_capacity)

            return todayscount < max_allowed

        elif offer.type_of_offer == "At certain sale position":
            todayscount = 0
            if selected_gift:
                todayscount = Customer.objects.filter(
                    date_of_purchase=today_date, gift=selected_gift
                ).count()

            sale_nums = offer.sale_numbers or []
            parsed_positions = []
            for num in sale_nums:
                try:
                    parsed_positions.append(int(num))
                except (ValueError, TypeError):
                    continue

            # Count how many milestone positions have unlocked at or before the current sales count.
            # If a position hit an ineligible customer, it remains unclaimed until the next eligible customer.
            positions_unlocked = sum(1 for p in parsed_positions if p <= sales_count)
            target_capacity = (
                offer.daily_quantity
                if offer.daily_quantity > 0
                else len(parsed_positions)
            )
            max_allowed = min(positions_unlocked, target_capacity)

            return todayscount < max_allowed

        return False

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True

        if not phone_model:
            return False

        phone_model_str = str(phone_model).strip()
        for condition in offer.valid_condition.all():
            cond_str = str(condition.condition).strip()
            if (
                phone_model_str.lower().startswith(cond_str.lower())
                or cond_str.lower() in phone_model_str.lower()
            ):
                return True

        return False


@api_view(["GET"])
def GetGiftList(request):
    lucky_draw_system_id = request.GET["lucky_draw_system_id"]
    category = request.GET.get("category")
    lucky_draw_system = LuckyDrawSystem.objects.get(id=lucky_draw_system_id)
    gifts = GiftItem.objects.filter(lucky_draw_system=lucky_draw_system)
    if category:
        gifts = gifts.filter(category=category)
    serializer = GiftItemSerializer(gifts, many=True)
    data = serializer.data
    for gift in data:
        if gift.get("image"):
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
        Customer.objects
        .filter(lucky_draw_system=lds)
        .order_by("-id")
        .values_list("id", flat=True)[:100]
    )

    # Aggregate counts of gifts from those customers via the M2M relation
    # Exclude customers without any assigned gift
    gift_counts = (
        Customer.objects
        .filter(id__in=last_ids, gift__isnull=False)
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

    return Response({
        "results": results,
        "total_customers_considered": len(last_ids),
    })


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def UploadImeiBulk(request):
    """
    Bulk upload IMEI numbers from a CSV file.
    Optimized for high-volume uploads (50,000+ records) using streaming file I/O,
    in-memory deduplication, and PostgreSQL chunked bulk_create with conflict ignoring.
    """
    if request.method != "POST":
        return Response(
            {"error": "Invalid request method. Please use POST method."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = (
        request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
    )
    if "file" not in payload and "file" in request.FILES:
        payload["file"] = request.FILES["file"]

    serializer = BulkUploadIMEISerializer(data=payload, context={"request": request})
    if not serializer.is_valid():
        first_field = next(iter(serializer.errors))
        first_err = serializer.errors[first_field]
        err_msg = (
            first_err[0]
            if isinstance(first_err, list) and first_err
            else str(first_err)
        )
        return Response(
            {"error": err_msg, "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_data = serializer.validated_data
    lucky_draw_system = validated_data["lucky_draw_system"]
    file_obj = validated_data["file"]
    batch_size = validated_data.get("batch_size", 5000)

    org = None
    if (
        hasattr(request, "user")
        and getattr(request.user, "is_authenticated", False)
        and hasattr(request.user, "organization")
        and request.user.organization
        and not getattr(request.user, "is_superuser", False)
    ):
        org = request.user.organization

    try:
        result = bulk_upload_imeis_from_csv(
            lucky_draw_system_id=lucky_draw_system.id,
            file_obj=file_obj,
            batch_size=batch_size,
            organization=org,
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        err_msg = (
            e.message
            if hasattr(e, "message")
            else (e.messages[0] if hasattr(e, "messages") and e.messages else str(e))
        )
        return Response(
            {"error": err_msg},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to upload IMEIs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class UploadImeiWithRegionBulkView(generics.GenericAPIView):
    """
    Bulk upload IMEI numbers with region from a CSV, TSV, or Excel (.xlsx, .xls) file.
    Expected columns:
      - 1st Column: IMEI (imei_no)
      - 2nd Column: Model Name (phone_model)
      - 3rd Column: Region (region)
    """

    serializer_class = BulkUploadIMEIWithRegionSerializer
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        payload = (
            request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        )
        if "file" not in payload and "file" in request.FILES:
            payload["file"] = request.FILES["file"]

        serializer = self.get_serializer(data=payload, context={"request": request})
        if not serializer.is_valid():
            first_field = next(iter(serializer.errors))
            first_err = serializer.errors[first_field]
            err_msg = (
                first_err[0]
                if isinstance(first_err, list) and first_err
                else str(first_err)
            )
            return Response(
                {"error": err_msg, "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        lucky_draw_system = validated_data["lucky_draw_system"]
        file_obj = validated_data["file"]
        batch_size = validated_data.get("batch_size", 5000)
        update_existing = validated_data.get("update_existing", False)

        org = None
        if (
            hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            and hasattr(request.user, "organization")
            and request.user.organization
            and not getattr(request.user, "is_superuser", False)
        ):
            org = request.user.organization

        try:
            result = bulk_upload_imeis_with_region_from_file(
                lucky_draw_system_id=lucky_draw_system.id,
                file_obj=file_obj,
                batch_size=batch_size,
                update_existing=update_existing,
                organization=org,
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            err_msg = (
                e.message
                if hasattr(e, "message")
                else (
                    e.messages[0] if hasattr(e, "messages") and e.messages else str(e)
                )
            )
            return Response(
                {"error": err_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to upload IMEIs with region: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


UploadImeiWithRegionBulk = UploadImeiWithRegionBulkView.as_view()


@api_view(["GET"])
def export_imei(request):
    if request.method == "GET":
        luckydraw = request.GET.get("lucky_draw_system_id", None)

        queryset = IMEINO.objects.all()
        if luckydraw is not None:
            system = LuckyDrawSystem.objects.get(id=luckydraw)
            queryset = queryset.filter(lucky_draw_system=system)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="imei.csv"'
        writer = csv.writer(response)
        writer.writerow(["IMEI", "Phone Model", "Region"])
        for imei in queryset:
            writer.writerow([imei.imei_no, imei.phone_model, imei.region or ""])
        return response
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
        writer.writerow([
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
        ])

        # Write the data rows
        for customer in queryset:
            writer.writerow([
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
            ])

        return response


def is_value_empty(val):
    if val is None or val == "":
        return True
    if isinstance(val, str) and val.strip().lower() in ("", "none", "null"):
        return True
    return False


def export_data(request, pk):
    luckydraw = LuckyDrawSystem.objects.get(id=pk)
    today_date = timezone.now().date()
    safe_name = slugify(luckydraw.name) if luckydraw.name else "luckydraw"

    cust = (
        Customer.objects
        .filter(lucky_draw_system=luckydraw)
        .prefetch_related("gift")
        .select_related("recharge_card")
    )

    filter_param = request.GET.get("filter")
    start_date_param = request.GET.get("start_date")
    end_date_param = request.GET.get("end_date")
    start_date = None
    end_date = None

    if start_date_param:
        try:
            start_date = datetime.datetime.strptime(start_date_param, "%Y-%m-%d").date()
        except ValueError:
            start_date = None

    if end_date_param:
        try:
            end_date = datetime.datetime.strptime(end_date_param, "%Y-%m-%d").date()
        except ValueError:
            end_date = None

    if start_date and end_date:
        if start_date == end_date:
            cust = cust.filter(date_of_purchase=start_date)
            date_str = f"{start_date}"
        else:
            cust = cust.filter(
                date_of_purchase__gte=start_date, date_of_purchase__lte=end_date
            )
            date_str = f"{start_date}_to_{end_date}"
    elif start_date:
        cust = cust.filter(date_of_purchase=start_date)
        date_str = f"{start_date}"
    elif end_date:
        cust = cust.filter(date_of_purchase__lte=end_date)
        date_str = f"to_{end_date}"
    elif filter_param == "today":
        cust = cust.filter(date_of_purchase=today_date)
        date_str = f"{today_date}"
    else:
        date_str = "all"

    filename = f"{safe_name}_{date_str}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    columns_def = [
        ("Date of Purchase", lambda c, g: c.date_of_purchase),
        ("Customer Name", lambda c, g: c.customer_name),
        ("Shop Name", lambda c, g: c.shop_name),
        ("Sold Area", lambda c, g: c.sold_area),
        ("Phone Number", lambda c, g: c.phone_number),
        ("Email", lambda c, g: c.email),
        ("Phone Model", lambda c, g: c.phone_model),
        ("IMEI", lambda c, g: c.imei),
        ("How Know About Campaign", lambda c, g: c.how_know_about_campaign),
        ("Profession", lambda c, g: c.profession),
        ("Region", lambda c, g: c.region),
        ("Gift", lambda c, g: ", ".join([gift.name for gift in g]) if g else ""),
        ("Prize Details", lambda c, g: c.prize_details),
    ]

    all_rows = []
    for customer in cust:
        gifts = list(customer.gift.all())
        row = [getter(customer, gifts) for _, getter in columns_def]
        all_rows.append(row)

    if all_rows:
        active_indices = [
            col_idx
            for col_idx in range(len(columns_def))
            if any(not is_value_empty(row[col_idx]) for row in all_rows)
        ]
    else:
        active_indices = list(range(len(columns_def)))

    headers = [columns_def[idx][0] for idx in active_indices]
    writer.writerow(headers)

    for row in all_rows:
        filtered_row = [row[idx] for idx in active_indices]
        writer.writerow(filtered_row)

    return response


class YachuCustomerListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Customer.objects.select_related("lucky_draw_system").filter(
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

        if not lucky_draw_system:
            return Response(
                {"error": "Lucky draw system is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lucky_draw = LuckyDrawSystem.objects.get(id=lucky_draw_system)
        except (LuckyDrawSystem.DoesNotExist, ValueError):
            return Response(
                {"error": "Invalid Lucky Draw System."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if lucky_draw.end_date < timezone.now().date():
            return Response(
                {"error": "Lucky draw campaign has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imei = request.data.get("imei")

        if not imei:
            return Response(
                {"error": "IMEI is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            imei_obj = IMEINO.objects.get(
                imei_no=imei, lucky_draw_system=lucky_draw, used=False
            )
        except IMEINO.DoesNotExist:
            return Response(
                {"error": "Invalid IMEI or IMEI already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_model = imei_obj.phone_model

        if Customer.objects.filter(imei=imei).exists():
            return Response(
                {"error": "A customer with this IMEI already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        how_know_about_campaign = request.data.get("how_know_about_campaign")
        profession = request.data.get("profession")

        imei_obj.used = True
        imei_obj.save()

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
        import random

        today_date = timezone.now().date()
        lucky_draw_system = customer.lucky_draw_system

        sales_today, _ = Sales.objects.get_or_create(
            date=today_date,
            lucky_draw_system=lucky_draw_system,
            defaults={"sales_count": 0},
        )
        sales_today.sales_count += 1
        sales_today.save()
        sales_count = sales_today.sales_count

        phone_model = customer.phone_model

        # Check restriction: if Yachu Lucky Draw (ID 3 or name contains 'Yachu Lucky Draw')
        # and sold area is Sankhamul, Bhaktapur, or Jhamsikhel, do not award Body Lotion.
        is_yachu_system = (
            str(lucky_draw_system.id) == "3"
            or "yachu" in (lucky_draw_system.name or "").lower()
        )
        sold_area_lower = (customer.sold_area or "").strip().lower()
        restricted_areas = ["sankhamul", "bhaktapur", "jhamsikhel"]
        restrict_body_lotion = is_yachu_system and any(
            area in sold_area_lower for area in restricted_areas
        )

        def is_body_lotion(gift_obj):
            if not gift_obj or not getattr(gift_obj, "name", None):
                return False
            name = gift_obj.name.lower().replace("-", " ")
            return "body lotion" in name or "bodylotion" in name

        # 1. FIXED OFFERS
        fixed_offer = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw_system, imei_no=customer.imei, quantity__gt=0
        ).first()

        if fixed_offer:
            available_gifts = [
                g
                for g in fixed_offer.gift.all()
                if not (restrict_body_lotion and is_body_lotion(g))
            ]
            if available_gifts:
                selected_gift = available_gifts[0]
                customer.gift.set([selected_gift])
                customer.prize_details = (
                    f"Congratulations! You've won {selected_gift.name}"
                )
                customer.save()
                fixed_offer.quantity -= 1
                fixed_offer.save()
                return

        # 2. FETCH ACTIVE OFFERS
        mobile_offers = list(
            MobilePhoneOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        electronic_offers = list(
            ElectronicsShopOffer.objects.filter(
                lucky_draw_system=lucky_draw_system,
                start_date__lte=today_date,
                end_date__gte=today_date,
                daily_quantity__gt=0,
            )
        )

        region_str = (
            customer.region
            if (customer.region and customer.region != "None")
            else "Other"
        )

        matching_offers = []

        for offer in mobile_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                if restrict_body_lotion and is_body_lotion(
                    getattr(offer, "gift", None)
                ):
                    continue
                matching_offers.append(offer)

        for offer in electronic_offers:
            if self.check_offer_condition(
                offer, sales_count, region_str
            ) and self.check_validto_condition(offer, phone_model):
                if restrict_body_lotion:
                    offer_gifts = list(offer.gift.all())
                    if offer_gifts and all(is_body_lotion(g) for g in offer_gifts):
                        continue
                matching_offers.append(offer)

        if matching_offers:
            selected_gift = None

            # CHECK IF ANY MATCHED OFFER HAS AN EXPLICIT PRIORITY (> 0)
            has_explicit_priority = any(
                getattr(o, "priority", 0) > 0 for o in matching_offers
            )

            if has_explicit_priority:
                # ROUTE A: PRIORITY 1 FIRST
                # Filter out offers with priority 0, then sort ASCENDING (1 -> 2 -> 3...)
                priority_offers = [
                    o for o in matching_offers if getattr(o, "priority", 0) > 0
                ]
                sorted_offers = sorted(
                    priority_offers, key=lambda x: getattr(x, "priority")
                )

                for offer in sorted_offers:
                    gifts = (
                        list(offer.gift.all())
                        if hasattr(offer.gift, "all")
                        else [getattr(offer, "gift", None)]
                    )

                    valid_options = []
                    for gift in gifts:
                        if not gift:
                            continue

                        if restrict_body_lotion and is_body_lotion(gift):
                            continue

                        already_assigned = Customer.objects.filter(
                            date_of_purchase=today_date, gift=gift
                        ).count()

                        target_capacity = max(offer.daily_quantity, 1)

                        if already_assigned < target_capacity:
                            assigned_ratio = already_assigned / target_capacity
                            valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]
                        selected_gift = random.choice(best_candidates)
                        break  # Stop immediately at Priority 1 (or lowest priority number matched)

            if not selected_gift:
                # ROUTE B: NORMAL EVALUATION (If no explicit priority matched or priority offers out of stock)
                offers_by_cv = {}
                for offer in matching_offers:
                    try:
                        cv = int(offer.offer_condition_value)
                    except (ValueError, TypeError):
                        cv = 1
                    offers_by_cv.setdefault(cv, []).append(offer)

                sorted_cvs = sorted(offers_by_cv.keys(), reverse=True)

                for cv in sorted_cvs:
                    valid_options = []
                    for offer in offers_by_cv[cv]:
                        gifts = (
                            list(offer.gift.all())
                            if hasattr(offer.gift, "all")
                            else [getattr(offer, "gift", None)]
                        )

                        for gift in gifts:
                            if not gift:
                                continue

                            if restrict_body_lotion and is_body_lotion(gift):
                                continue

                            already_assigned = Customer.objects.filter(
                                date_of_purchase=today_date, gift=gift
                            ).count()

                            target_capacity = max(offer.daily_quantity, 1)

                            if already_assigned < target_capacity:
                                assigned_ratio = already_assigned / target_capacity
                                valid_options.append((gift, assigned_ratio))

                    if valid_options:
                        min_ratio = min(item[1] for item in valid_options)
                        best_candidates = [
                            gift
                            for gift, ratio in valid_options
                            if ratio <= (min_ratio + 0.01)
                        ]

                        if best_candidates:
                            selected_gift = random.choice(best_candidates)
                            break

            if selected_gift and not (
                restrict_body_lotion and is_body_lotion(selected_gift)
            ):
                customer.gift.set([selected_gift])
                if (
                    "thank you" in selected_gift.name.lower()
                    or "better luck" in selected_gift.name.lower()
                ):
                    customer.prize_details = "Thank you for your purchase!"
                else:
                    customer.prize_details = (
                        f"Congratulations! You've won {selected_gift.name}"
                    )
                customer.save()
                return

        # 3. FALLBACK FOR UNMATCHED SPINS / EXHAUSTED CAPS
        better_luck_gift = GiftItem.objects.filter(
            lucky_draw_system=lucky_draw_system, name__icontains="thank you"
        ).first()

        if better_luck_gift:
            customer.gift.set([better_luck_gift])
            customer.prize_details = "Thank you for your purchase!"
        else:
            customer.prize_details = "Thank you for your purchase!"

        customer.save()

    def check_offer_condition(self, offer, sales_count, region):
        today_date = timezone.now().date()
        today_time = timezone.now().time()

        if hasattr(offer, "gift") and hasattr(offer.gift, "all"):
            selected_gift = offer.gift.first()
        else:
            selected_gift = getattr(offer, "gift", None)

        # 1. Target region exclusivity check
        target_regions_str = getattr(offer, "target_regions", None)
        if target_regions_str:
            allowed_regions = [
                r.strip().lower() for r in target_regions_str.split(",") if r.strip()
            ]
            if (
                not region
                or region in ("None", "Other")
                or region.strip().lower() not in allowed_regions
            ):
                return False

        # 2. Region balancing check
        if offer.has_region_limit:
            if region == "None" or region == "Other":
                return False
            if not selected_gift:
                return False

            region_counts = {
                "Centeral Region": Customer.objects.filter(
                    region="Centeral Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
                "Eastern Region": Customer.objects.filter(
                    region="Eastern Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
                "Western Region": Customer.objects.filter(
                    region="Western Region",
                    gift=selected_gift,
                    date_of_purchase=today_date,
                ).count(),
            }
            min_count = min(region_counts.values())
            if region_counts.get(region, 0) > min_count:
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

            try:
                cond_val = int(offer.offer_condition_value)
            except (ValueError, TypeError):
                cond_val = 1

            # Cumulative unlocked gifts based on intervals reached so far today.
            # If an earlier interval was reached by an ineligible customer (e.g. from another region),
            # the prize remains unawarded and rolls over to the next eligible customer.
            intervals_reached = (sales_count // cond_val) if cond_val > 0 else 0
            target_capacity = (
                offer.daily_quantity if offer.daily_quantity > 0 else intervals_reached
            )
            max_allowed = min(intervals_reached, target_capacity)

            return todayscount < max_allowed

        elif offer.type_of_offer == "At certain sale position":
            todayscount = 0
            if selected_gift:
                todayscount = Customer.objects.filter(
                    date_of_purchase=today_date, gift=selected_gift
                ).count()

            sale_nums = offer.sale_numbers or []
            parsed_positions = []
            for num in sale_nums:
                try:
                    parsed_positions.append(int(num))
                except (ValueError, TypeError):
                    continue

            # Count how many milestone positions have unlocked at or before the current sales count.
            # If a position hit an ineligible customer, it remains unclaimed until the next eligible customer.
            positions_unlocked = sum(1 for p in parsed_positions if p <= sales_count)
            target_capacity = (
                offer.daily_quantity
                if offer.daily_quantity > 0
                else len(parsed_positions)
            )
            max_allowed = min(positions_unlocked, target_capacity)

            return todayscount < max_allowed

        return False

    def check_validto_condition(self, offer, phone_model):
        if not offer.valid_condition.exists():
            return True

        if not phone_model:
            return False

        phone_model_str = str(phone_model).strip()
        for condition in offer.valid_condition.all():
            cond_str = str(condition.condition).strip()
            if (
                phone_model_str.lower().startswith(cond_str.lower())
                or cond_str.lower() in phone_model_str.lower()
            ):
                return True

        return False
