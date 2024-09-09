from django.urls import path
from . import views

urlpatterns = [
    # GiftItem URLs
    path('gift-items/', views.GiftItemSerializerView.as_view(), name='gift-item-list-create'),

    # LuckyDrawSystem URLs
    path('lucky-draw-systems/', views.LuckyDrawSystemSerializerView.as_view(), name='luckydrawsystem-list-create'),
    path('lucky-draw-systems/<int:pk>/', views.LuckyDrawSystemRetrieveUpdateDestroyView.as_view(), name='luckydrawsystem-detail'),

    # RechargeCard URLs
    path('recharge-cards/', views.RechargeCardSerializerView.as_view(), name='recharge-card-list-create'),

    # IMEINO URLs
    path('imei-numbers/', views.IMEINOSerializerView.as_view(), name='imeino-list-create'),

    # FixOffer URLs
    path('fix-offers/', views.FixOfferSerializerView.as_view(), name='fix-offer-list-create'),

    # MobileOfferType URLs
    path('mobile-offer-types/', views.MobileOfferTypeSerializerView.as_view(), name='mobile-offer-type-list-create'),

    # MobilePhoneOffer URLs
    path('mobile-phone-offers/', views.MobilePhoneOfferSerializerView.as_view(), name='mobile-phone-offer-list-create'),

    # RechargeCardOffer URLs
    path('recharge-card-offers/', views.RechargeCardOfferSerializerView.as_view(), name='recharge-card-offer-list-create'),

    # Customer URLs
    path('customers/', views.CustomerSerializerView.as_view(), name='customer-list-create'),
]