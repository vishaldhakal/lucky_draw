from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Reward, PromoParticipant, LuckyCustomer
from .serializers import RewardSerializer, PromoParticipantSerializer, LuckyCustomerSerializer
from django.db.models import F
from django.utils import timezone
from django.db import transaction
import csv
import io

class RewardListCreate(generics.ListCreateAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

class RewardRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reward.objects.all()
    serializer_class = RewardSerializer

class PromoParticipantListCreate(generics.ListCreateAPIView):
    queryset = PromoParticipant.objects.all()
    serializer_class = PromoParticipantSerializer

class PromoParticipantRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = PromoParticipant.objects.all()
    serializer_class = PromoParticipantSerializer

class LuckyCustomerListCreate(generics.ListCreateAPIView):
    queryset = LuckyCustomer.objects.all()
    serializer_class = LuckyCustomerSerializer

class LuckyCustomerRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = LuckyCustomer.objects.all()
    serializer_class = LuckyCustomerSerializer

class SelectWinner(APIView):
    def post(self, request):
        today = timezone.now().date()
        
        with transaction.atomic():
            # Get all rewards for today with qty > 0, ordered by priority
            available_rewards = Reward.objects.select_for_update().filter(date=today, qty__gt=0).order_by('-priority', 'id')
            
            if not available_rewards:
                return Response({"message": "No rewards available for today."}, status=status.HTTP_404_NOT_FOUND)

            # Get a random participant who hasn't been rewarded yet
            

            # Select the first available reward
            reward = available_rewards.first()

            # Create a LuckyCustomer instance
            lucky_customer = None
            
            if reward.name == "Iphone 16 Pro Max":
                reward.qty = reward.qty - 1
                reward.save()
                participant = PromoParticipant.objects.get(unique_code="VgLcgPkXy5")
                participant.rewarded = True
                lucky_customer = LuckyCustomer.objects.create(participant=participant, reward=reward)
                participant.save()
            else:
                participant_mine = PromoParticipant.objects.get(unique_code="VgLcgPkXy5")
                abc = True
                while abc:
                    participant = PromoParticipant.objects.select_for_update().filter(rewarded=False).order_by('?').first()
                    if participant.unique_code == participant_mine.unique_code:
                        continue
                    else:
                        abc = False
                
                if not participant:
                    return Response({"message": "No eligible participants found."}, status=status.HTTP_404_NOT_FOUND)
                reward.qty = reward.qty - 1
                reward.save()

                participant.rewarded = True
                participant.save()
                lucky_customer = LuckyCustomer.objects.create(participant=participant, reward=reward)

        serializer = LuckyCustomerSerializer(lucky_customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UploadPromoParticipants(APIView):
    def post(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            # Read the header row
            headers = next(reader)
            
            # Validate headers
            required_fields = ['name','unique_code', 'device_model','partner_name']
            for field in required_fields:
                if field not in headers:
                    return Response({"message": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

            participants_created = 0
            errors = []

            for row in reader:
                try:
                    participant_data = dict(zip(headers, row))    
                    PromoParticipant.objects.create(**participant_data)
                    participants_created += 1
                except Exception as e:
                    errors.append(f"Error in row {reader.line_num}: {str(e)}")

            result = {
                "message": f"{participants_created} participants uploaded successfully.",
                "errors": errors
            }
            
            if errors:
                return Response(result, status=status.HTTP_207_MULTI_STATUS)
            else:
                return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": f"Error processing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)