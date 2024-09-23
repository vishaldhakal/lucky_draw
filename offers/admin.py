from django.contrib import admin
from unfold.admin import ModelAdmin
from . models import *
from tinymce.widgets import TinyMCE
# Register your models here.

admin.site.register(GiftItem, ModelAdmin)
class LuckyDrawSystemAdmin(ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE,},
    }
admin.site.register(LuckyDrawSystem, LuckyDrawSystemAdmin)

admin.site.register(Sales, ModelAdmin)
admin.site.register(RechargeCard, ModelAdmin)
admin.site.register(RechargeCardOffer, ModelAdmin)
admin.site.register(FixOffer, ModelAdmin)
class MobilePhoneOfferAdmin(ModelAdmin):
    fieldsets=(
        (None,{'fields':('lucky_draw_system',('start_date','end_date'),'gift','daily_quantity','type_of_offer','offer_condition_value','sale_numbers','valid_condition','priority')}),
    )
admin.site.register(MobilePhoneOffer, MobilePhoneOfferAdmin)
admin.site.register(IMEINO, ModelAdmin)
admin.site.register(Customer, ModelAdmin)
admin.site.register(MobileOfferCondition, ModelAdmin)
admin.site.register(RechargeCardCondition, ModelAdmin)
admin.site.register(ElectronicsShopOffer, ModelAdmin)
admin.site.register(ElectronicOfferCondition, ModelAdmin)


