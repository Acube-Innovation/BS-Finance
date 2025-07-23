# Python rounds decimals to the nearest even number if the decimal point is 0.5 . Since payroll running requires all 0.5 s to be rounded up always this function is used

from decimal import Decimal, ROUND_HALF_UP

def round_half_up(value, digits=0):
    """
    Rounds a number using the round-half-up method (i.e., 0.5 always rounds up).

    :param value: The number to round
    :param digits: Number of decimal places to round to (default: 0)
    :return: Rounded number
    """
    if value is None:
        return 0
    return float(Decimal(str(value)).quantize(
        Decimal('1.' + '0'*digits) if digits else Decimal('1'),
        rounding=ROUND_HALF_UP
    ))
