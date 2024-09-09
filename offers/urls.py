from django.urls import path
from .views import (
    GiftItemSerializerView,
    LuckyDrawSystemSerializerView,
    LuckyDrawSystemRetrieveUpdateDestroyView,
    RechargeCardSerializerView,
    IMEINOSerializerView,
    FixOfferSerializerView,
    BaseOfferSerializerView,
    MobilePhoneOfferSerializerView,
    RechargeCardOfferSerializerView,
    CustomerSerializerView
)

urlpatterns = [
    # GiftItem URLs
    path('gift-items/', GiftItemSerializerView.as_view(), name='gift-item-list-create'),

    # LuckyDrawSystem URLs
    path('lucky-draw-systems/', LuckyDrawSystemSerializerView.as_view(), name='luckydrawsystem-list-create'),
    path('lucky-draw-systems/<int:pk>/', LuckyDrawSystemRetrieveUpdateDestroyView.as_view(), name='luckydrawsystem-retrieve-update-destroy'),

    # RechargeCard URLs
    path('recharge-cards/', RechargeCardSerializerView.as_view(), name='recharge-card-list-create'),

    # IMEINO URLs
    path('imei-numbers/', IMEINOSerializerView.as_view(), name='imeino-list-create'),

    # FixOffer URLs
    path('fix-offers/', FixOfferSerializerView.as_view(), name='fix-offer-list-create'),

    # BaseOffer URLs
    path('base-offers/', BaseOfferSerializerView.as_view(), name='base-offer-list-create'),

    # MobilePhoneOffer URLs
    path('mobile-phone-offers/', MobilePhoneOfferSerializerView.as_view(), name='mobile-phone-offer-list-create'),

    # RechargeCardOffer URLs
    path('recharge-card-offers/', RechargeCardOfferSerializerView.as_view(), name='recharge-card-offer-list-create'),

    # Customer URLs
    path('customers/', CustomerSerializerView.as_view(), name='customer-list-create'),
]