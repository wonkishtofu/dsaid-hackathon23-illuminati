def to_bearing(a):
    """ Takes the azimuth angle, which should be 0-360 degrees, and returns a string N/E/S/W.
    North is 0 degrees."""
    
    while a > 360:
        a -= 360
    while a < 0:
        a += 360
    
    if a >= 348.75 or a < 11.25:
        return "N"
    elif a >= 11.25 and a < 33.75:
        return "NNE"
    elif a >= 33.75 and a < 56.25:
        return "NE"
    elif a >= 56.25 and a < 78.75:
        return "ENE"
    elif a >= 78.75 and a < 101.25:
        return "E"
    elif a >= 101.25 and a < 123.75:
        return "ESE"
    elif a >= 123.75 and a < 146.25:
        return "SE"
    elif a >= 146.25 and a < 168.75:
        return "SSE"
    elif a >= 168.75 and a < 191.25:
        return "S"
    elif a >= 191.25 and a < 213.75:
        return "SSW"
    elif a >= 213.75 and a < 236.25:
        return "SW"
    elif a >= 236.25 and a < 258.75:
        return "WSW"
    elif a >= 258.75 and a < 281.25:
        return "W"
    elif a >= 281.25 and a < 303.75:
        return "WNW"
    elif a >= 303.75 and a < 326.25:
        return "NW"
    elif a >= 326.25 and a < 348.75:
        return "NNW"
    else:
        return "Unknown"
