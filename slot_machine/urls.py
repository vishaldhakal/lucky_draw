from django.urls import path
from .views import SlotMachineListCreateView,GetGifts

urlpatterns = [
    path('slot-machine/', SlotMachineListCreateView.as_view(), name='customer-list-create'),
    path('gifts/', GetGifts, name='get-gifts'),

]