from django.urls import path
from . import views

urlpatterns = [
    # GiftItem URLs
    path('gift-items/', views.GiftItemListCreateView.as_view(), name='gift-item-list-create'),
    path('gift-items/<int:pk>/', views.GiftItemRetrieveUpdateDestroyView.as_view(), name='gift-item-detail'),

    # LuckyDrawSystem URLs
    path('lucky-draw-systems/', views.LuckyDrawSystemListCreateView.as_view(), name='luckydrawsystem-list-create'),
    path('lucky-draw-systems/<int:pk>/', views.LuckyDrawSystemRetrieveUpdateDestroyView.as_view(), name='luckydrawsystem-detail'),

    # RechargeCard URLs
    path('recharge-cards/', views.RechargeCardListCreateView.as_view(), name='recharge-card-list-create'),
    path('recharge-cards/<int:pk>/', views.RechargeCardRetrieveUpdateDestroyView.as_view(), name='recharge-card-detail'),

    # IMEINO URLs
    path('imei-numbers/', views.IMEINOListCreateView.as_view(), name='imeino-list-create'),
    path('imei-numbers/<int:pk>/', views.IMEINORetrieveUpdateDestroyView.as_view(), name='imeino-detail'),

    # FixOffer URLs
    path('fix-offers/', views.FixOfferListCreateView.as_view(), name='fix-offer-list-create'),
    path('fix-offers/<int:pk>/', views.FixOfferRetrieveUpdateDestroyView.as_view(), name='fix-offer-detail'),

    # MobileOfferType URLs
    path('mobile-offer-condition/', views.MobileOfferConditionListCreateView.as_view(), name='mobile-offer-condition-list-create'),
    path('mobile-offer-condition/<int:pk>/', views.MobileOfferConditionRetrieveUpdateDestroyView.as_view(), name='mobile-offer-condition-detail'),

    # MobilePhoneOffer URLs
    path('mobile-phone-offers/', views.MobilePhoneOfferListCreateView.as_view(), name='mobile-phone-offer-list-create'),
    path('mobile-phone-offers/<int:pk>/', views.MobileOfferConditionRetrieveUpdateDestroyView.as_view(), name='mobile-phone-offer-detail'),

    # RechargeCardOffer URLs
    path('recharge-card-offers/', views.RechargeCardOfferListCreateView.as_view(), name='recharge-card-offer-list-create'),
    path('recharge-card-offers/<int:pk>/', views.RechargeCardOfferRetrieveUpdateDestroyView.as_view(), name='recharge-card-offer-detail'),

    # Customer URLs
    path('customers/', views.CustomerListCreateView.as_view(), name='customer-list-create'),
]