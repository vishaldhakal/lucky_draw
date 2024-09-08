from rest_framework import serializers
from .models import GiftItem,LuckyDrawSystem

class GiftItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftItem
        fields = '__all__'

class LuckyDrawSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LuckyDrawSystem
        fields = ['organization','name','description','']