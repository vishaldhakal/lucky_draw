from django.contrib import admin
from django.db import models
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import (
    IMEINO,
    Customer,
    ElectronicOfferCondition,
    ElectronicsShopOffer,
    FixOffer,
    GiftItem,
    LuckyDrawSystem,
    MobileOfferCondition,
    MobilePhoneOffer,
    RechargeCard,
    RechargeCardCondition,
    RechargeCardOffer,
    Sales,
)

# Register your models here.


class GiftItemAdmin(ModelAdmin):
    list_display = ("name", "category", "lucky_draw_system")
    list_filter = ("lucky_draw_system", "category")
    search_fields = ["name"]  # or whichever fields should be searchable


admin.site.register(GiftItem, GiftItemAdmin)


class LuckyDrawSystemAdmin(ModelAdmin):
    list_display = ("name", "type", "id", "start_date", "end_date")
    formfield_overrides = {
        models.TextField: {
            "widget": TinyMCE,
        },
    }


admin.site.register(LuckyDrawSystem, LuckyDrawSystemAdmin)

admin.site.register(Sales, ModelAdmin)
admin.site.register(RechargeCard, ModelAdmin)
admin.site.register(RechargeCardOffer, ModelAdmin)
admin.site.register(FixOffer, ModelAdmin)


class MobilePhoneOfferAdmin(ModelAdmin):
    list_display = (
        "type_of_offer",
        "gift",
        "lucky_draw_system",
        "offer_condition_value",
        "daily_quantity",
        "start_date",
        "end_date",
    )
    list_editable = ("offer_condition_value", "daily_quantity")
    list_filter = ("lucky_draw_system",)
    autocomplete_fields = ["gift"]
    list_select_related = ("gift", "gift__lucky_draw_system", "lucky_draw_system")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "lucky_draw_system",
                    ("start_date", "end_date"),
                    "gift",
                    "daily_quantity",
                    "type_of_offer",
                    "offer_condition_value",
                    "sale_numbers",
                    "valid_condition",
                    "priority",
                    "start_time",
                    "end_time",
                    "has_time_limit",
                    "has_region_limit",
                )
            },
        ),
    )


class CustomerAdmin(ModelAdmin):
    list_filter = (
        "lucky_draw_system",
        "sale_status",
        "region",
        "how_know_about_campaign",
        "date_of_purchase",
    )
    list_display = (
        "customer_name",
        "imei",
        "prize_details",
        "region",
        "date_of_purchase",
    )
    search_fields = ("customer_name", "imei", "prize_details", "region")


admin.site.register(MobilePhoneOffer, MobilePhoneOfferAdmin)


class IMEIAdmin(ModelAdmin):
    search_fields = ("imei_no",)


admin.site.register(IMEINO, IMEIAdmin)

admin.site.register(Customer, CustomerAdmin)
admin.site.register(MobileOfferCondition, ModelAdmin)
admin.site.register(RechargeCardCondition, ModelAdmin)
admin.site.register(ElectronicOfferCondition, ModelAdmin)


class ElectronicsShopOfferAdmin(ModelAdmin):
    list_display = (
        "type_of_offer",
        "get_gifts",  # custom method
        "lucky_draw_system",
        "offer_condition_value",
        "daily_quantity",
        "start_date",
        "end_date",
    )
    list_editable = ("offer_condition_value", "daily_quantity")
    list_filter = ("lucky_draw_system",)
    autocomplete_fields = ["gift"]  # <--- searchable dropdown for gifts
    list_select_related = ("lucky_draw_system",)

    def get_gifts(self, obj):
        # Join names of related gifts into a string
        return ", ".join([str(g) for g in obj.gift.all()])

    get_gifts.short_description = "Gifts"


admin.site.register(ElectronicsShopOffer, ElectronicsShopOfferAdmin)
