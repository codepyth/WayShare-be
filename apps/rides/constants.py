from django.db import models


class TripStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    FULL = "full", "Full"
    DEPARTED = "departed", "Departed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class BookingStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    EXPIRED = "expired", "Expired"
    CANCELLED_BY_PASSENGER = "cancelled_by_passenger", "Cancelled by Passenger"
    CANCELLED_BY_DRIVER = "cancelled_by_driver", "Cancelled by Driver"
    TRAVELLED = "travelled", "Travelled"
    COMPLETED = "completed", "Completed"
    DISPUTED = "disputed", "Disputed"


class ParcelStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    ACCEPTED = "accepted", "Accepted"
    COLLECTED = "collected", "Collected"
    IN_TRANSIT = "in_transit", "In Transit"
    DELIVERED = "delivered", "Delivered"
    CONFIRMED = "confirmed", "Confirmed"