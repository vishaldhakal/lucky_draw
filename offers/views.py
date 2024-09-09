from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import GiftItemSerializer,LuckyDrawSystemSerializer,RechargeCardSerializer,IMEINOSerializer,FixOfferSerializer,BaseOfferSerializer,MobilePhoneOfferSerializer,RechargeCardOfferSerializer,CustomerSerializer
from .models import Sales,GiftItem,LuckyDrawSystem,RechargeCard,IMEINO,FixOffer,BaseOffer,MobilePhoneOffer,RechargeCardOffer,ElectronicsShopOffer,Customer

# Create your views here.

class GiftItemSerializerView(generics.ListCreateAPIView):

    queryset = GiftItem.objects.all()
    serializer_class = GiftItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GiftItem.objects.filter(organization=self.request.user.organization)

    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        name=request.data.get('name')
        image=request.data.get('image')

        gift_item = GiftItem.objects.create(
            lucky_draw_system=lucky_draw_system,
            name=name,
            image=image
        )
        gift_item.save()
        serializer = GiftItemSerializer(gift_item)
        return Response(serializer.data)

class LuckyDrawSystemSerializerView(generics.ListCreateAPIView):    
    serializer_class = LuckyDrawSystemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LuckyDrawSystem.objects.filter(organization=self.request.user.organization)

    def create(self, request, *args, **kwargs):
        organization = request.data.get('organization')
        name = request.data.get('name')
        description = request.data.get('description')
        background_image=request.data.get('background_image')
        hero_image=request.data.get('hero_image')
        main_offer_stamp_image=request.data.get('main_offer_stamp_image')
        qr=request.data.get('qr')
        type=request.data.get('type')
        start_date=request.data.get('start_date')
        end_date=request.data.get('end_date')

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
            end_date=end_date
        )
        lucky_draw_system.save()
        serializer = LuckyDrawSystemSerializer(lucky_draw_system)
        return Response(serializer.data)

class RechargeCardSerializerView(generics.ListCreateAPIView):
    serializer_class = RechargeCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return RechargeCard.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        name=request.data.get('name')
        image=request.data.get('image')

        recharge_card = RechargeCard.objects.create(
            lucky_draw_system=lucky_draw_system,
            name=name,
            image=image
        )
        recharge_card.save()
        serializer = RechargeCardSerializer(recharge_card)
        return Response(serializer.data)

class IMEINOSerializerView(generics.ListCreateAPIView):
    serializer_class = IMEINOSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return IMEINO.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        imei_no=request.data.get('imei_no')
        phone_model=request.data.get('phone_model')

        imeino = IMEINO.objects.create(
            lucky_draw_system=lucky_draw_system,
            imei_no=imei_no,
            phone_model=phone_model
        )
        imeino.save()
        serializer = IMEINOSerializer(imeino)
        return Response(serializer.data)

class FixOfferSerializerView(generics.ListCreateAPIView):
    serializer_class = FixOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return FixOffer.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        imei_no=request.data.get('imei_no')
        quantity=request.data.get('quantity')

        fix_offer = FixOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            imei_no=imei_no,
            quantity=quantity
        )
        fix_offer.save()
        serializer = FixOfferSerializer(fix_offer)
        return Response(serializer.data)


class BaseOfferSerializerView(generics.ListCreateAPIView):
    serializer_class = BaseOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return BaseOffer.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        name=request.data.get('name')
        image=request.data.get('image')

        base_offer = BaseOffer.objects.create(
            lucky_draw_system=lucky_draw_system,
            name=name,
            image=image
        )
        base_offer.save()
        serializer = BaseOfferSerializer(base_offer)
        return Response(serializer.data)
    
class MobilePhoneOfferSerializerView(generics.ListCreateAPIView):
    serializer_class = MobilePhoneOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        gift=self.request.data.get('gift')
        return MobilePhoneOffer.objects.filter(gift=gift)
    
    def create(self, request, *args, **kwargs):
        gift = request.data.get('gift')
        per_day=request.data.get('per_day')
        validto=request.data.get('validto')
        priority=request.data.get('priority')

        mobile_phone_offer = MobilePhoneOffer.objects.create(
            gift=gift,
            per_day=per_day,
            validto=validto,
            priority=priority
        )
        mobile_phone_offer.save()
        serializer = MobilePhoneOfferSerializer(mobile_phone_offer)
        return Response(serializer.data)

class RechargeCardOfferSerializerView(generics.ListCreateAPIView):
    serializer_class = RechargeCardOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        recharge_card=self.request.data.get('recharge_card')
        return RechargeCardOffer.objects.filter(RechargeCard=recharge_card)
    
    def create(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        provider=request.data.get('provider')

        recharge_card_offer = RechargeCardOffer.objects.create(
            amount=amount,
            provider=provider
        )
        recharge_card_offer.save()
        serializer = RechargeCardOfferSerializer(recharge_card_offer)
        return Response(serializer.data)
    
class CustomerSerializerView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return Customer.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):

        lucky_draw_system = request.data.get('lucky_draw_system')
        customer_name=request.data.get('customer_name')
        shop_name=request.data.get('shop_name')
        sold_area=request.data.get('sold_area')
        phone_number=request.data.get('phone_number')
        if Customer.objects.filter(phone_number=phone_number).exists():
            return Response(
                {"error": "A customer with this phone number already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prize_details=request.data.get('prize_details')
        imei=request.data.get('imei')

        try:
            imei_obj = IMEINO.objects.get(imei_no=imei, used=False)
        except IMEINO.DoesNotExist:
            return Response(
                {"error": "Invalid IMEI or IMEI already used."},
                status=status.HTTP_400_BAD_REQUEST
            )

        imeii=IMEINO.objects.get(imei_no=imei)
        phone_model=imeii.phone_model

        if Customer.objects.filter(imei=imei).exists():
            return Response(
                {"error": "A customer with this IMEI already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        how_know_about_campaign=request.data.get('how_know_about_campaign')
        profession=request.data.get('profession')

        imei_obj.used=True
        imei_obj.save()

        today_date=timezone.now().date()
        sale_today, created = Sales.objects.get_or_create(date=today_date)
        sale_today.sales_count += 1
        sale_today.save()

        customer = Customer.objects.create(
            lucky_draw_system=lucky_draw_system,
            customer_name=customer_name,
            shop_name=shop_name,
            sold_area=sold_area,
            phone_number=phone_number,
            phone_model=phone_model,
            prize_details=prize_details,
            imei=imei,
            how_know_about_campaign=how_know_about_campaign,
            profession=profession
        )
        customer.save()

        self.assign_gift(customer, imei, phone_model, sale_today.sales_count, today_date, lucky_draw_system)

        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def assign_gift(self,customer,imei,phone_model,sales_count,today_date,lucky_draw_system):
        #Fixed Offers
        fix_offer=FixOffer.objects.filter(lucky_draw_system=lucky_draw_system,quantiy__gt=0)
        for offer in fix_offer:
            if imei in offer.imei_no:
                customer.gift = offer.gift
                customer.prize_details = f"Congartulations! You've won {offer.gift.name}"
                customer.save()
                offer.quantity -= 1
                offer.save()
                return
        
        #Mobile Phone Offers
        mobile_offers = MobilePhoneOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            start_date__lte=today_date,
            end_date__gte=today_date
        ).order_by('priority')

        for offer in mobile_offers:
            condition_met = False
            if offer.type_of_offer == "After every certain sale":
                condition_met = sales_count % int(offer.offer_condition_value) == 0
            elif offer.type_of_offer == "At certain sale position":
                condition_met = sales_count == int(offer.offer_condition_value)
            elif offer.type_of_offer in ["Weekly Offer", "Monthly Offer"]:
                condition_met = True

            validto_check = offer.validto.condition == "All" or phone_model.startswith(offer.validto.condition)

            if condition_met and validto_check and offer.quantity > 0:
                customer.gift = offer.gift
                customer.prize_details = f"Congratulations! You've won {offer.gift.name}"
                customer.save()
                offer.quantity -= 1
                offer.save()
                return
        
        #Recharge Card Offers
        recharge_offers = RechargeCardOffer.objects.filter(
            lucky_draw_system=lucky_draw_system,
            start_date__lte=today_date,
            end_date__gte=today_date
        )
        for offer in recharge_offers:
            if ((offer.type_of_offer == "After every certain sale" and sales_count % int(offer.offer_condition_value) == 0) or
                (offer.type_of_offer == "At certain sale position" and sales_count == int(offer.offer_condition_value)) or
                offer.type_of_offer in ["Weekly Offer", "Monthly Offer"]) and offer.quantity > 0:
                
                recharge_card = RechargeCard.objects.filter(
                    lucky_draw_system=lucky_draw_system,
                    provider=offer.provider,
                    amount=offer.amount,
                    is_assigned=False
                ).first()

                if recharge_card:
                    customer.recharge_card=recharge_card
                    customer.amount_of_card=offer.amount
                    customer.prize_details = f"Congratulations! You've won {offer.provider} recharge card worth {offer.amount}"
                    customer.save()
                    recharge_card.is_assigned = True
                    recharge_card.save()
                    offer.quantity -= 1
                    offer.save()
                    return
        customer.prize_details = "Thank you for your purchase!"
        customer.save()

                





