from fractions import Fraction

from paladin.rationals import AUDIO_SPEED, TARGET_RATE, VIDEO_SCALE, nearest_intermediate_rate, parse_rate


def test_canonical_ratios_are_exact():
    assert TARGET_RATE == Fraction(24000, 1001)
    assert VIDEO_SCALE == Fraction(25025, 24000)
    assert AUDIO_SPEED == Fraction(24000, 25025)


def test_rate_parsing_and_audio_rate():
    assert parse_rate("24000/1001") == Fraction(24000, 1001)
    assert nearest_intermediate_rate(48000) == 46034
