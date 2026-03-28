from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Cities"
        unique_together = ('name', 'country')

    def __str__(self):
        return f"{self.name} ({self.country.name})"

class Task(models.Model):
    name = models.CharField(max_length=200)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True) # Added
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)       # Added
    engine = models.CharField(
        max_length=50,
        choices=[
            ('engine_a', 'Engine A'),
            ('engine_b', 'Engine B'),
            ('engine_c', 'Engine C'),
        ],
        blank=True,
        null=True
    )
    params = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
