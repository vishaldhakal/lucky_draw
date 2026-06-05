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
