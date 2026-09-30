from rest_framework import serializers

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
    RechargeCardCondition,
    RechargeCardOffer,
)


class GiftItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = GiftItem
        fields = "__all__"

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        return None


class GetOrganiazationDetail(serializers.ModelSerializer):
    class Meta:
        model = LuckyDrawSystem
        fields = "__all__"
        depth = 1


class LuckyDrawSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LuckyDrawSystem
        fields = [
            "id",
            "name",
            "description",
            "background_image",
            "hero_image",
            "main_offer_stamp_image",
            "qr",
            "type",
            "start_date",
            "end_date",
            "how_to_participate",
            "redeem_condition",
            "terms_and_conditions",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RechargeCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeCard
        fields = ["lucky_draw_system", "cardno", "provider", "amount", "is_assigned"]


class IMEINOSerializer(serializers.ModelSerializer):
    class Meta:
        model = IMEINO
        fields = ["lucky_draw_system", "imei_no", "phone_model"]


class FixOfferSerializer(serializers.ModelSerializer):
    gift = serializers.PrimaryKeyRelatedField(
        many=True, queryset=GiftItem.objects.all()
    )

    class Meta:
        model = FixOffer
        fields = ["lucky_draw_system", "imei_no", "quantity", "gift"]


class MobileOfferConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileOfferCondition
        fields = ["id", "offer_condition_name", "condition"]


class MobilePhoneOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePhoneOffer
        exclude = ["lucky_draw_system"]
        depth = 1


class RechargeCardOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeCardOffer
        fields = "__all__"


class RechargeCardConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeCardCondition
        fields = "__all__"


class ElectronicShopOfferConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronicOfferCondition
        fields = "__all__"


class ElectronicsShopOfferSerializer(serializers.ModelSerializer):
    gift = serializers.PrimaryKeyRelatedField(
        many=True, queryset=GiftItem.objects.all()
    )

    class Meta:
        model = ElectronicsShopOffer
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "lucky_draw_system",
            "customer_name",
            "shop_name",
            "sold_area",
            "phone_number",
            "product_purchased",
            "bill_number",
            "phone_model",
            "imei",
            "date_of_purchase",
            "how_know_about_campaign",
            "profession",
        ]


class CustomerGiftSerializer(serializers.ModelSerializer):
    gift = GiftItemSerializer(many=True)

    class Meta:
        model = Customer
        fields = [
            "customer_name",
            "shop_name",
            "sold_area",
            "phone_number",
            "product_purchased",
            "bill_number",
            "phone_model",
            "imei",
            "gift",
            "email",
            "date_of_purchase",
        ]

    def to_representation(self, instance):
        self.fields["gift"].context.update(self.context)
        return super().to_representation(instance)


class BulkDeleteLuckyDrawIMEISerializer(serializers.Serializer):
    lucky_draw_system = serializers.PrimaryKeyRelatedField(
        queryset=LuckyDrawSystem.objects.all(),
        required=True,
        help_text="Select Lucky Draw System.",
    )
    only_unused = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If True, only delete unused IMEI numbers (used=False). Default is False (delete all).",
    )
    batch_size = serializers.IntegerField(
        required=False,
        default=5000,
        min_value=0,
        max_value=50000,
        help_text="Chunk size for batch deletion (0 for single atomic query). Default is 5000.",
    )

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)

        # Support aliases like lucky_draw_system_id or system_id
        if "lucky_draw_system" not in data or data["lucky_draw_system"] in ("", None):
            if "lucky_draw_system_id" in data and data["lucky_draw_system_id"] not in ("", None):
                data["lucky_draw_system"] = data["lucky_draw_system_id"]
            elif "system_id" in data and data["system_id"] not in ("", None):
                data["lucky_draw_system"] = data["system_id"]

        return super().to_internal_value(data)

    def validate_lucky_draw_system(self, value):
        request = self.context.get("request")
        if (
            request
            and hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            and hasattr(request.user, "organization")
            and request.user.organization
            and not getattr(request.user, "is_superuser", False)
        ):
            if value.organization_id != request.user.organization.id:
                raise serializers.ValidationError(
                    "You do not have permission to delete IMEIs for this lucky draw system."
                )
        return value


class BulkUploadIMEISerializer(serializers.Serializer):
    lucky_draw_system = serializers.PrimaryKeyRelatedField(
        queryset=LuckyDrawSystem.objects.all(),
        required=True,
        error_messages={
            "required": "Invalid Lucky Draw System.",
            "does_not_exist": "Invalid Lucky Draw System.",
            "incorrect_type": "Invalid Lucky Draw System.",
            "null": "Invalid Lucky Draw System.",
        },
        help_text="Select Lucky Draw System.",
    )
    file = serializers.FileField(
        required=True,
        error_messages={
            "required": "CSV file is required.",
            "empty": "CSV file is required.",
            "null": "CSV file is required.",
        },
        help_text="CSV file containing IMEI numbers.",
    )
    batch_size = serializers.IntegerField(
        required=False,
        default=5000,
        min_value=500,
        max_value=25000,
        help_text="Batch size for bulk insertion (default: 5000).",
    )

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)

        # Support aliases like lucky_draw_system_id or system_id
        if "lucky_draw_system" not in data or data["lucky_draw_system"] in ("", None):
            if "lucky_draw_system_id" in data and data["lucky_draw_system_id"] not in ("", None):
                data["lucky_draw_system"] = data["lucky_draw_system_id"]
            elif "system_id" in data and data["system_id"] not in ("", None):
                data["lucky_draw_system"] = data["system_id"]

        return super().to_internal_value(data)

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Invalid file format. Please upload a CSV file.")
        if value.size == 0:
            raise serializers.ValidationError("The uploaded CSV file is empty.")
        return value

    def validate_lucky_draw_system(self, value):
        request = self.context.get("request")
        if (
            request
            and hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            and hasattr(request.user, "organization")
            and request.user.organization
            and not getattr(request.user, "is_superuser", False)
        ):
            if value.organization_id != request.user.organization.id:
                raise serializers.ValidationError(
                    "You do not have permission to upload IMEIs for this lucky draw system."
                )
        return value




