from django.db import models


class Item(models.Model):
	class Category(models.TextChoices):
		FRUIT = "FRUIT", "Fruit"
		VEGETABLE = "VEGETABLE", "Vegetable"
		PREPARED = "PREPARED", "Prepared Food"

	name = models.CharField(max_length=100, unique=True)
	category = models.CharField(max_length=16, choices=Category.choices)
	unit = models.CharField(max_length=16, default="unit")
	weight_per_unit_kg = models.FloatField(default=1.0)

	def __str__(self) -> str:
		return f"{self.name} ({self.category})"


class Store(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location_lat = models.FloatField()
    location_lng = models.FloatField()

    def __str__(self) -> str:
        return self.name

