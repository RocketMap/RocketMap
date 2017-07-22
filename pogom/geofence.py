#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import timeit
import logging

from .utils import get_args

log = logging.getLogger(__name__)

args = get_args()

# Trying to import matplotlib, which is not compatible with all hardware.
# Matlplotlib is faster for big calculations.
try:
    from matplotlib.path import Path
except ImportError as e:
    # Pass as this is an optional requirement. We're going to check later if it
    # was properly imported and only use it if it's installed.
    pass


class Geofences:
    def __init__(self):
        self.geofenced_areas = []
        self.excluded_areas = []
        self.use_matplotlib = 'matplotlib' in sys.modules

        if args.geofence_file or args.geofence_excluded_file:
            log.info('Loading geofenced or excluded areas.')
            self.geofenced_areas = self.parse_geofences_file(
                args.geofence_file, excluded=False)
            self.excluded_areas = self.parse_geofences_file(
                args.geofence_excluded_file, excluded=True)
            log.info('Loaded %d geofenced and %d excluded areas.',
                     len(self.geofenced_areas),
                     len(self.excluded_areas))

    def is_enabled(self):
        return (self.geofenced_areas or self.excluded_areas)

    def get_geofenced_coordinates(self, coordinates):
        log.info('Using matplotlib: %s.', self.use_matplotlib)
        log.info('Found %d coordinates to geofence.', len(coordinates))
        geofenced_coordinates = []
        startTime = timeit.default_timer()
        for c in coordinates:
            # Coordinate is not valid if in one excluded area.
            if self._is_excluded(c):
                continue

            # Coordinate is geofenced if in one geofenced area.
            if self.geofenced_areas:
                for va in self.geofenced_areas:
                    if self._in_area(c, va):
                        geofenced_coordinates.append(c)
                        break
            else:
                geofenced_coordinates.append(c)

        elapsedTime = timeit.default_timer() - startTime
        log.info('Geofenced to %s coordinates in %.2fs.',
                 len(geofenced_coordinates), elapsedTime)
        return geofenced_coordinates

    def _is_excluded(self, coordinate):
        for ea in self.excluded_areas:
            if self._in_area(coordinate, ea):
                return True

        return False

    def _in_area(self, coordinate, area):
        if args.spawnpoint_scanning:
            point = {'lat': coordinate['lat'], 'lon': coordinate['lng']}
        else:
            point = {'lat': coordinate[0], 'lon': coordinate[1]}
        polygon = area['polygon']
        if self.use_matplotlib:
            return self.is_point_in_polygon_matplotlib(point, polygon)
        else:
            return self.is_point_in_polygon_custom(point, polygon)

    @staticmethod
    def parse_geofences_file(geofence_file, excluded):
        geofences = []
        # Read coordinates of excluded areas from file.
        if geofence_file:
            with open(geofence_file) as f:
                for line in f:
                    line = line.strip()
                    if len(line) == 0:  # Empty line.
                        continue
                    elif line.startswith("["):  # Name line.
                        name = line.replace("[", "").replace("]", "")
                        geofences.append({
                            'excluded': excluded,
                            'name': name,
                            'polygon': []
                        })
                        log.debug('Found geofence: %s.', name)
                    else:  # Coordinate line.
                        lat, lon = line.split(",")
                        LatLon = {'lat': float(lat), 'lon': float(lon)}
                        geofences[-1]['polygon'].append(LatLon)

        return geofences

    @staticmethod
    def is_point_in_polygon_matplotlib(point, polygon):
        pointTuple = (point['lat'], point['lon'])
        polygonTupleList = []
        for c in polygon:
            coordinateTuple = (c['lat'], c['lon'])
            polygonTupleList.append(coordinateTuple)

        polygonTupleList.append(polygonTupleList[0])
        path = Path(polygonTupleList)
        return path.contains_point(pointTuple)

    @staticmethod
    def is_point_in_polygon_custom(point, polygon):
        # Initialize first coordinate as default.
        maxLat = polygon[0]['lat']
        minLat = polygon[0]['lat']
        maxLon = polygon[0]['lon']
        minLon = polygon[0]['lon']

        for coords in polygon:
            maxLat = max(coords['lat'], maxLat)
            minLat = min(coords['lat'], minLat)
            maxLon = max(coords['lon'], maxLon)
            minLon = min(coords['lon'], minLon)

        if ((point['lat'] > maxLat) or (point['lat'] < minLat) or
                (point['lon'] > maxLon) or (point['lon'] < minLon)):
            return False

        inside = False
        lat1, lon1 = polygon[0]['lat'], polygon[0]['lon']
        N = len(polygon)
        for n in range(1, N+1):
            lat2, lon2 = polygon[n % N]['lat'], polygon[n % N]['lon']
            if (min(lon1, lon2) < point['lon'] <= max(lon1, lon2) and
                    point['lat'] <= max(lat1, lat2)):
                        if lon1 != lon2:
                            latIntersection = (
                                (point['lon'] - lon1) *
                                (lat2 - lat1) / (lon2 - lon1) +
                                lat1)

                        if lat1 == lat2 or point['lat'] <= latIntersection:
                            inside = not inside

            lat1, lon1 = lat2, lon2

        return inside
