from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp_points = models.IntegerField(default=0)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invites')

    def __str__(self):
        return self.user.email

class Group(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, default=uuid.uuid4().hex[:8])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CarbonSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    electricity_kwh = models.FloatField()
    region = models.CharField(max_length=100)
    transport_km = models.FloatField()
    vehicle_type = models.CharField(max_length=50)
    flights_per_year = models.IntegerField()
    flight_class = models.CharField(max_length=50)
    grocery_spend = models.FloatField()
    diet_type = models.CharField(max_length=50)
    purchase_spend = models.FloatField()
    purchase_category = models.CharField(max_length=100)
    home_type = models.CharField(max_length=50)
    household_size = models.IntegerField()
    total_emissions = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"