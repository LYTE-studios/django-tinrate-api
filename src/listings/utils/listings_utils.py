def minutes_to_hours(minutes):
    """
    Convert minutes to hours with one decimal place.
    
    Args:
        minutes (int | float): Number of minutes
    
    Returns:
        float: Equivalent hours rounded to one decimal place.
    """
    if minutes is None:
        return 0.0
    if not isinstance(minutes, (int, float)):
        raise ValueError("minutes must be a number")

    return round(minutes / 60, 1)
