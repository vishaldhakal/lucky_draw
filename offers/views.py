from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import GiftItemSerializer,LuckyDrawSystemSerializer,RechargeCardSerializer,IMEINOSerializer,FixOfferSerializer,MobileOfferConditionSerializer,MobilePhoneOfferSerializer,RechargeCardOfferSerializer,CustomerSerializer
from .models import Sales,GiftItem,LuckyDrawSystem,RechargeCard,IMEINO,FixOffer,BaseOffer,MobilePhoneOffer,RechargeCardOffer,ElectronicsShopOffer,Customer,MobileOfferCondition

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
    
class LuckyDrawSystemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LuckyDrawSystemSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LuckyDrawSystem.objects.filter(organization=self.request.user.organization)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Get the data from the request
        name = request.data.get('name')
        description = request.data.get('description')
        background_image = request.data.get('background_image')
        hero_image = request.data.get('hero_image')
        main_offer_stamp_image = request.data.get('main_offer_stamp_image')
        qr = request.data.get('qr')
        type = request.data.get('type')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

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
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lucky_draw_system=self.request.data.get('lucky_draw_system')
        return IMEINO.objects.filter(lucky_draw_system=lucky_draw_system)
    
    def create(self, request, *args, **kwargs):
        lucky_draw_system = request.data.get('lucky_draw_system')
        imei_no=request.data.get('imei_no')
        phone_model=request.data.get('phone_model')
        lucky_draw=LuckyDrawSystem.objects.get(id=lucky_draw_system)

        imeino = IMEINO.objects.create(
            lucky_draw_system=lucky_draw,
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

class MobileOfferConditionSerializerView(generics.ListCreateAPIView):
    serializer_class = MobileOfferConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MobileOfferCondition.objects.all()
    
    def create(self, request, *args, **kwargs):
        offer_type_name = request.data.get('offer_type_name')
        condition = request.data.get('condition')

        mobile_type = MobileOfferCondition.objects.create(
            offer_type_name=offer_type_name,
            condition=condition
        )
        mobile_type.save()
        serializer = MobileOfferConditionSerializer(mobile_type)
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
    # permission_classes = [IsAuthenticated]

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
        
        
        imei=request.data.get('imei')

        if not imei:
            return Response({"error": "IMEI is required."}, status=status.HTTP_400_BAD_REQUEST)
        print (imei)
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

        lucky_draw=LuckyDrawSystem.objects.get(id=lucky_draw_system)

        customer = Customer.objects.create(
            lucky_draw_system=lucky_draw,
            customer_name=customer_name,
            shop_name=shop_name,
            sold_area=sold_area,
            phone_number=phone_number,
            phone_model=phone_model,
            imei=imei,
            how_know_about_campaign=how_know_about_campaign,
            profession=profession
        )
        # customer.save()

        self.assign_gift(customer)
      
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def assign_gift(self,customer):
        today=timezone.now().date()
        lucky_draw_system=customer.lucky_draw_system

        sales_today,created = Sales.objects.get_or_create(
            date=today,
            lucky_draw_system=lucky_draw_system,
            defaults={
                'sales_count':0
            }
        )
        
        #Fixed Offers
        fix_offer=FixOffer.objects.filter(lucky_draw_system=lucky_draw_system,quantity__gt=0)
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

                





