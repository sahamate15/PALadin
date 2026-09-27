from fractions import Fraction

TARGET_RATE = Fraction(24000, 1001)
SOURCE_RATE = Fraction(25, 1)
VIDEO_SCALE = SOURCE_RATE / TARGET_RATE
AUDIO_SPEED = TARGET_RATE / SOURCE_RATE


def parse_rate(value: str | None) -> Fraction | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            if int(denominator) == 0:
                return None
            return Fraction(int(numerator), int(denominator))
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def nearest_intermediate_rate(sample_rate: int, ratio: Fraction = AUDIO_SPEED) -> int:
    return round(sample_rate * ratio)
