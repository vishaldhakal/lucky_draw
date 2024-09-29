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
        (None,{'fields':('lucky_draw_system',('start_date','end_date'),'gift','daily_quantity','type_of_offer','offer_condition_value','sale_numbers','valid_condition','priority','start_time','end_time','has_time_limit','has_region_limit')}),
    )
class CustomerAdmin(ModelAdmin):
    list_filter = ('lucky_draw_system','sale_status', 'region', 'how_know_about_campaign','date_of_purchase')
    list_display = ('customer_name','imei','prize_details','region','gift')
    search_fields = ('customer_name','imei','prize_details','region','gift')

admin.site.register(MobilePhoneOffer, MobilePhoneOfferAdmin)

class IMEIAdmin(ModelAdmin):
    search_fields = ('imei_no',)

admin.site.register(IMEINO, IMEIAdmin)

admin.site.register(Customer, CustomerAdmin)
admin.site.register(MobileOfferCondition, ModelAdmin)
admin.site.register(RechargeCardCondition, ModelAdmin)
admin.site.register(ElectronicOfferCondition, ModelAdmin)


