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


def _days360(start_date, end_date, european=True):
    """
    DAYS360 day-count:
      - european=True  -> European method (both 31st => 30)
      - european=False -> US (NASD) method
    """
    y1, m1, d1 = start_date.year, start_date.month, start_date.day
    y2, m2, d2 = end_date.year,   end_date.month,   end_date.day

    if european:
        if d1 == 31: d1 = 30
        if d2 == 31: d2 = 30
    else:
        # US (NASD) method
        if d1 == 31: d1 = 30
        if d2 == 31:
            if d1 < 30:
                d2 = 1
                m2 += 1
                if m2 > 12:
                    m2 = 1
                    y2 += 1
            else:
                d2 = 30

    return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)