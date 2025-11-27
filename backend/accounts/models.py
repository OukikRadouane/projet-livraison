from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models


class User(AbstractUser):
	class Roles(models.TextChoices):
		CUSTOMER = "CUSTOMER", "Customer"
		COURIER = "COURIER", "Courier"

	role = models.CharField(
		max_length=16, choices=Roles.choices, default=Roles.CUSTOMER
	)
	capacity_kg = models.PositiveIntegerField(default=10, validators=[MaxValueValidator(10)])
	phone = models.CharField(max_length=32, blank=True, default="")
	cne = models.CharField(max_length=32, blank=True, default="")
	location_lat = models.FloatField(null=True, blank=True)
	location_lng = models.FloatField(null=True, blank=True)

	def is_courier(self) -> bool:
		return self.role == self.Roles.COURIER

