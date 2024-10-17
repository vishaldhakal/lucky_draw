from rest_framework import serializers
from .models import Reward, PromoParticipant, LuckyCustomer

class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = '__all__'

class PromoParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoParticipant
        fields = '__all__'

class LuckyCustomerSerializer(serializers.ModelSerializer):
    participant = PromoParticipantSerializer(read_only=True)
    reward = RewardSerializer(read_only=True)

    class Meta:
        model = LuckyCustomer
        fields = '__all__'