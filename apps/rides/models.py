from django.db import models
from django.db.models import F, Q
from apps.core.models import BaseModel


class City(BaseModel):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=100, unique=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table            = "cities"
        verbose_name_plural = "cities"
        ordering            = ("name",)

    def __str__(self):
        return self.name


class PickupPoint(BaseModel):
    city        = models.ForeignKey(City, on_delete=models.PROTECT, related_name="pickup_points")
    name        = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table    = "pickup_points"
        ordering    = ("city__name", "name")
        constraints = (
            models.UniqueConstraint(fields=("city", "name"), name="unique_pickup_point_per_city"),
        )

    def __str__(self):
        return f"{self.name}, {self.city}"


class RouteDistance(BaseModel):
    origin_city         = models.ForeignKey(City, on_delete=models.PROTECT, related_name="routes_from")
    destination_city    = models.ForeignKey(City, on_delete=models.PROTECT, related_name="routes_to")
    miles               = models.DecimalField(max_digits=5, decimal_places=1)

    class Meta:
        db_table    = "route_distances"
        ordering    = ("origin_city__name", "destination_city__name")
        constraints = (
            models.UniqueConstraint(fields=("origin_city", "destination_city"), name="unique_route"),
            models.CheckConstraint(condition=~Q(origin_city=F("destination_city")), name="route_cities_differ"),
            models.CheckConstraint(condition=Q(miles__gt=0), name="route_miles_positive"),
        )

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city}: {self.miles} mi"
    