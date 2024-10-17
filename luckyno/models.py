from django.db import models

class Reward(models.Model):
    PRIORITY_CHOICES = (
         ('High', 'High'),
         ('Low', 'Low')
    )
    name = models.CharField(max_length=100)
    qty = models.IntegerField(default=0)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Low')
    date = models.DateField()

    def __str__(self):
        return self.name

class PromoParticipant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=150)
    imei = models.BigIntegerField(unique=True)
    location = models.CharField(max_length=255)
    rewarded = models.BooleanField(default=False)
    unique_code = models.CharField(max_length=100, unique=True)
    submitted_on = models.DateTimeField(auto_now_add=True)
    device_model = models.CharField(max_length=200)
    activated = models.CharField(max_length=300,default='Yes')
    activation_date = models.DateField(null=True, blank=True)
    partner_name = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.name} - {self.unique_code}"

    class Meta:
        ordering = ['-submitted_on']

class LuckyCustomer(models.Model):
    participant = models.ForeignKey(PromoParticipant, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    won_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant.name} - {self.reward.name}"

    class Meta:
        ordering = ['-won_on']