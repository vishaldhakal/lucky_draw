from django.contrib import admin
from unfold.admin import ModelAdmin
from . models import *
# Register your models here.
admin.site.register(GiftItem, ModelAdmin)
admin.site.register(LuckyDrawSystem, ModelAdmin)
admin.site.register(Sales, ModelAdmin)
admin.site.register(RechargeCard, ModelAdmin)
admin.site.register(RechargeCardOffer, ModelAdmin)
admin.site.register(FixOffer, ModelAdmin)
admin.site.register(MobilePhoneOffer, ModelAdmin)
admin.site.register(IMEINO, ModelAdmin)
admin.site.register(Customer, ModelAdmin)

