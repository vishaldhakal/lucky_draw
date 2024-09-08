from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from .serializers import GiftItemSerializer
from .models import GiftItem

# Create your views here.

class GiftItemSerializerView(generics.CreateAPIView):
    queryset = GiftItem.objects.all()
    serializer_class = GiftItemSerializer