from django.urls import path
from . import views
urlpatterns = [
    path('add-gift/',views.GiftItemSerializerView.as_view(),name='add-gift'),
]
