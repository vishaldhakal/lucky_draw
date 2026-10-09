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
        "priority",
        "target_regions",
        "start_date",
        "end_date",
    )
    list_editable = ("offer_condition_value", "daily_quantity", "priority")
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
                    "target_regions",
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
        "sold_area",
        "date_of_purchase",
    )
    list_display = (
        "customer_name",
        "imei",
        "prize_details",
        "region",
        "sold_area",
        "date_of_purchase",
    )
    search_fields = ("customer_name", "imei", "prize_details", "region", "sold_area")


admin.site.register(MobilePhoneOffer, MobilePhoneOfferAdmin)


class IMEIAdmin(ModelAdmin):
    list_display = ("imei_no", "phone_model", "region", "lucky_draw_system", "used")
    list_editable = ("used",)
    list_filter = ("used", "lucky_draw_system", "region")
    search_fields = ("imei_no", "phone_model", "region")
    list_select_related = ("lucky_draw_system",)


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
        "target_regions",
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
