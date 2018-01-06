from math import acos, atan2, cos, degrees, radians, sin, sqrt

R = 6378137.0


def distance(pos1, pos2):
    if pos1 == pos2:
        return 0.0

    lat1 = radians(pos1[0])
    lon1 = radians(pos1[1])
    lat2 = radians(pos2[0])
    lon2 = radians(pos2[1])

    a = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1)

    if a > 1:
        return 0.0

    return acos(a) * R


def intermediate_point(pos1, pos2, f):
    if pos1 == pos2:
        return pos1

    lat1 = radians(pos1[0])
    lon1 = radians(pos1[1])
    lat2 = radians(pos2[0])
    lon2 = radians(pos2[1])

    a = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1)

    if a > 1:  # too close
        return pos1 if f < 0.5 else pos2

    delta = acos(a)

    if delta == 0:  # too close
        return pos1 if f < 0.5 else pos2

    a = sin((1 - f) * delta) / delta
    b = sin(f * delta) / delta
    x = a * cos(lat1) * cos(lon1) + b * cos(lat2) * cos(lon2)
    y = a * cos(lat1) * sin(lon1) + b * cos(lat2) * sin(lon2)
    z = a * sin(lat1) + b * sin(lat2)

    lat3 = atan2(z, sqrt(x**2 + y**2))
    lon3 = atan2(y, x)

    def normalize(pos):
        return ((pos[0] + 540) % 360) - 180, ((pos[1] + 540) % 360) - 180

    return normalize((degrees(lat3), degrees(lon3)))
