from django.contrib import admin
from .models import Reward, PromoParticipant, LuckyCustomer
from unfold.admin import ModelAdmin

class PromoParticipantAdmin(ModelAdmin):
    list_display = ('name', 'email', 'unique_code', 'rewarded', 'submitted_on')
    search_fields = ('name', 'email', 'unique_code')
    list_filter = ('rewarded', 'activated', 'partner_name')

admin.site.register(Reward,ModelAdmin)
admin.site.register(PromoParticipant, PromoParticipantAdmin)
admin.site.register(LuckyCustomer,ModelAdmin)