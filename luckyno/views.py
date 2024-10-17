from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Reward, PromoParticipant, LuckyCustomer
from .serializers import RewardSerializer, PromoParticipantSerializer, LuckyCustomerSerializer
from django.db.models import F
from django.utils import timezone
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
        
        # Get all rewards for today with qty > 0, ordered by priority
        available_rewards = Reward.objects.filter(date=today, qty__gt=0).order_by('-priority', 'id')
        
        if not available_rewards:
            return Response({"message": "No rewards available for today."}, status=status.HTTP_404_NOT_FOUND)

        # Get a random participant who hasn't been rewarded yet
        participant = PromoParticipant.objects.filter(rewarded=False).order_by('?').first()
        
        if not participant:
            return Response({"message": "No eligible participants found."}, status=status.HTTP_404_NOT_FOUND)

        # Select the first available reward
        reward = available_rewards.first()

        # Create a LuckyCustomer instance
        lucky_customer = LuckyCustomer.objects.create(participant=participant, reward=reward)

        # Update the reward quantity and participant status
        reward.qty = F('qty') - 1
        reward.save()

        participant.rewarded = True
        participant.save()

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
            required_fields = ['name', 'email', 'phone_number', 'imei', 'location', 'unique_code', 'device_model', 'activated', 'partner_name']
            for field in required_fields:
                if field not in headers:
                    return Response({"message": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

            participants_created = 0
            errors = []

            for row in reader:
                try:
                    participant_data = dict(zip(headers, row))
                    
                    # Handle activation_date separately
                    activation_date = participant_data.pop('activation_date', None)
                    if activation_date:
                        participant_data['activation_date'] = activation_date
                    
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