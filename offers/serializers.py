from rest_framework import serializers
from .models import GiftItem,LuckyDrawSystem,RechargeCard,IMEINO,FixOffer,BaseOffer,MobilePhoneOffer,RechargeCardOffer,ElectronicsShopOffer,Customer

class GiftItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftItem
        fields = '__all__'

class LuckyDrawSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LuckyDrawSystem
        fields = ['organization','name','description','background_image','hero_image','main_offer_stamp_image','qr','type','start_date','end_date']
        read_only_fields = ['created_at','updated_at']

class RechargeCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeCard
        fields = ['lucky_draw_system','cardno','provider','amount']

class IMEINOSerializer(serializers.ModelSerializer):
    class Meta:
        model = IMEINO
        fields = ['lucky_draw_system','imei_no','phone_model']

class FixOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixOffer
        fields = ['lucky_draw_system','imei_no','quantity','gift']

class BaseOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseOffer
        fields = '__all__'

class MobilePhoneOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobilePhoneOffer
        fields = '__all__'

class RechargeCardOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeCardOffer
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['lucky_draw_system','customer_name','shop_name','sold_area','phone_number','phone_model','prize_details','imei','date_of_purchase','how_know_about_campaign','profession']