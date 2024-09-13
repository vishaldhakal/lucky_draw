from django.db import models
from account.models import Organization
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Sales(models.Model):
    sales_count = models.IntegerField(default=0)
    date = models.DateField(
        auto_now=False, auto_created=False, auto_now_add=False)
    lucky_draw_system= models.ForeignKey('LuckyDrawSystem', on_delete=models.CASCADE, related_name='sales')

    def __str__(self):
        return str(self.sales_count)

class LuckyDrawSystem(models.Model):
    LUCKY_DRAW_TYPE_CHOICES = [
        ('Mobile Phone Brand', 'Mobile Phone Brand'),
        ('Electronics Shop', 'Electronics Shop'),
        ('Other Shop', 'Other Shop'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    background_image = models.FileField(upload_to='lucky_draws/', blank=True, null=True)
    hero_image = models.FileField(upload_to='lucky_draws/', blank=True, null=True)
    main_offer_stamp_image = models.FileField(upload_to='lucky_draws/', blank=True, null=True)
    hero_title=models.CharField(max_length=255,default='')
    hero_subtitle=models.CharField(max_length=255,default='')
    qr = models.FileField(upload_to='lucky_draws/', blank=True, null=True)
    type = models.CharField(max_length=20, choices=LUCKY_DRAW_TYPE_CHOICES)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    start_date = models.DateField()
    end_date = models.DateField()
    uuid_key=models.CharField(max_length=255,unique=True,default='')

    def __str__(self):
        return self.name

class GiftItem(models.Model):
    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE, related_name='gift_items')
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='gift_items/', blank=True, null=True)

    def __str__(self):
        return self.name

class RechargeCard(models.Model):
    AMOUNT_CHOICES = [(50, "50"), (100, "100"), (200, "200"), (500, "500")]
    PROVIDER_CHOICES = [
        ("Ncell", "Ncell"),
        ("Ntc", "Ntc"),
        ("Smart Cell", "Smart Cell"),
        ("Others", "Others"),
    ]
    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE, related_name='recharge_cards')
    cardno = models.CharField(max_length=400, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    amount = models.IntegerField(choices=AMOUNT_CHOICES)
    is_assigned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.provider} - {self.cardno}"

class IMEINO(models.Model):
    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE, related_name='imei_numbers')
    imei_no = models.CharField(max_length=400, unique=True)
    phone_model = models.CharField(max_length=400, blank=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.imei_no

class FixOffer(models.Model):
    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE, related_name='fix_offers')
    imei_no = models.CharField(max_length=400)
    quantity = models.PositiveIntegerField()
    gift = models.ForeignKey(GiftItem, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.imei_no} - {self.gift.name}"

class BaseOffer(models.Model):
    OFFER_CHOICES = [
        ("After every certain sale", "After every certain sale"),
        ("At certain sale position", "At certain sale position")
    ]

    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_quantity = models.PositiveIntegerField(default=0)
    type_of_offer = models.CharField(max_length=30, choices=OFFER_CHOICES)
    offer_condition_value = models.CharField(max_length=500, blank=True)
    sale_numbers = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def is_valid_date(self):
        return self.start_date <= timezone.now().date() <= self.end_date

class MobileOfferCondition(models.Model):
    offer_condition_name=models.CharField(max_length=100)
    condition=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.offer_type_name} (Condition: {self.condition})"

class MobilePhoneOffer(BaseOffer):
    gift = models.ForeignKey(GiftItem, on_delete=models.CASCADE)
    valid_condition = models.ManyToManyField(MobileOfferCondition, blank=True)
    priority = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Offer on {self.gift.name}"

    class Meta:
        ordering = ("start_date", "priority")

class RechargeCardCondition(models.Model):
    offer_condition_name=models.CharField(max_length=100)
    condition=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.offer_type_name} (Condition: {self.condition})"


class RechargeCardOffer(BaseOffer):
    amount = models.IntegerField(choices=RechargeCard.AMOUNT_CHOICES, default=50)
    provider = models.CharField(max_length=20, choices=RechargeCard.PROVIDER_CHOICES, default="Ncell")
    valid_condition= models.ManyToManyField(RechargeCardCondition, blank=True)

    def __str__(self):
        return f"Offer on {self.provider} of {self.amount} Recharge card [ {self.quantity} ]"

    class Meta:
        ordering = ("start_date",)

class ElectronicOfferCondition(models.Model):
    offer_condition_name=models.CharField(max_length=100)
    condition=models.CharField(max_length=100)

    def __str__(self):
        return f"{self.offer_type_name} (Condition: {self.condition})"

class ElectronicsShopOffer(BaseOffer):
    gift=models.ForeignKey(GiftItem, on_delete=models.CASCADE)
    valid_condition=models.ManyToManyField(ElectronicOfferCondition,blank=True)
    def __str__(self):
        return f"Offer on Electronics Shop [ {self.quantity} ]"

    class Meta:
        ordering = ("start_date",)

class Customer(models.Model):
    CAMPAIGN_CHOICES = [
        ("Facebook Ads", "Facebook Ads"),
        ("Retail Shop", "Retail Shop"),
        ("Google Ads", "Google Ads"),
        ("Others", "Others"),
    ]

    lucky_draw_system = models.ForeignKey(LuckyDrawSystem, on_delete=models.CASCADE, related_name='customers')
    customer_name = models.CharField(max_length=400)
    shop_name = models.TextField()
    sold_area = models.CharField(max_length=800)
    phone_number = models.CharField(max_length=20)
    phone_model = models.CharField(max_length=400)
    sale_status = models.CharField(max_length=20, default="SOLD")
    prize_details = models.CharField(max_length=900, default="Thank You")
    gift = models.ForeignKey(GiftItem, on_delete=models.SET_NULL, null=True)
    imei = models.CharField(max_length=400, blank=True)
    date_of_purchase = models.DateField(auto_now_add=True)
    how_know_about_campaign = models.CharField(max_length=20, choices=CAMPAIGN_CHOICES)
    recharge_card = models.ForeignKey(RechargeCard, on_delete=models.SET_NULL, null=True, related_name="customers")
    ntc_recharge_card = models.BooleanField(default=False)
    amount_of_card = models.PositiveIntegerField(default=50, validators=[MinValueValidator(50), MaxValueValidator(500)])
    profession = models.CharField(max_length=400, default="None")

    def __str__(self):
        return self.customer_name

    class Meta:
        ordering = ("-date_of_purchase",)