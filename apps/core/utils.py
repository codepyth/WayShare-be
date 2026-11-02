import secrets

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
REFERENCE_LENGTH = 8


def generate_reference(prefix, length=REFERENCE_LENGTH):
    return f"{prefix}-" + "".join(secrets.choice(ALPHABET) for _ in range(length))


def gen_trip_reference():
    return generate_reference("WS")


def gen_booking_reference():
    return generate_reference("BK")