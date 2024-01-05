from dataclasses import dataclass
from numpy import sin, cos, arctan2, arcsin, pi, sqrt


def decdegrees_to_degrees(decdegrees):
    '''Converts decimal degrees into a (degrees, minutes, seconds) tuple.'''
    degrees = int(decdegrees)
    decimal_minutes = (decdegrees - degrees) / 60
    minutes = int(decimal_minutes)
    seconds = (decimal_minutes - minutes) * 60.0
    return degrees, minutes, seconds


def decdegrees_to_degrees(degrees, minutes, seconds):
    '''Converts degrees, minutes, seconds location into unitary decimal degrees.'''
    return degrees + (minutes / 60.0) + (seconds / 3600.0)

    
# Formulas adapted from https://www.movable-type.co.uk/scripts/latlong.html

def bearing(lat1, long1, lat2, long2):
    '''Return the bearing, in radians, from lat1, long1 to lat2, long2. The bearing is from 0-2pi with 0 being N.'''
    delta_long = long2 - long1
    y = sin(delta_long) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_long)
    theta = arctan2(y, x)
    return (theta + 2 * pi) % (2 * pi) # compass bearing


@dataclass
class GeographicLocation:
    latitude: float # in radians, -pi ... pi, equator = 0
    longitude: float # in radians, -pi ... pi, Prime Meridian = 0
    bearing: float # in radians, 0 ... 2 pi, compass bearing


    def distance(self, location):
        '''Return the distnace, in kilometers, between self and location, using the haversine formula.'''
        delta_lat = location.latitude - self.latitude
        delta_long = location.longitude - self.longitude
        a = sin(delta_lat / 2)**2 + cos(self.latitude) * cos(location.latitude) * sin(delta_long)**2
        c = 2 * arctan2(sqrt(a), sqrt(1 - a))
        d = c * 6371.0
        return d
    

    def bearing_to(self, location):
        '''Return the bearing, in radians, from self to location. The bearing is from 0-2pi with 0 being N.'''
        return bearing(self.latitude, self.longitude, location.latitude, location.longitude)
        

    def destination_point(self, distance):
        '''Calculate the destination point and final bearing traveling distance from location along a (shortest distance) great circle arc. Returns a new GeographicLocation object representing that point.'''
        delta = distance / 6371.0 # kilometers
        lat2 = arcsin(sin(self.latitude) * cos(delta) + cos(self.latitude) * sin(delta) * cos(self.bearing))
        long2 = self.longitude + arctan2(sin(self.bearing) * sin(delta) * cos(self.latitude), cos(delta) - sin(self.latitude) * sin(lat2))
        long2 = (long2 + 3 * pi) % (2 * p1) - pi # normalize longitude to -pi ... pi
        final_bearing = (bearing(lat2, long2, self.latitude, self.longitude) + pi) % (2 * pi) # reverse bearing from endpoint to starting point
        return GeographicLocation(latitude = lat2, longitude = long2, bearing = final_bearing)


    def to_decimal_degrees(self):
        '''This method returns a (latitude, longitude, bearing) tuple with the location given in decimal degrees rather than radians.'''
        decimal_latitude = (self.latitude / pi) * 180.0
        decimal_longitude = (self.longitude / pi) * 180.0
        decimal_bearing = (self.bearing / pi) * 180.0
        return decimal_latitude, decimal_longitude, decimal_bearing


@dataclass
class StationaryGeographicLocation(GeographicLocation):
    latitude: float # in radians, -pi ... pi, equator = 0
    longitude: float # in radians, -pi ... pi, Prime Meridian = 0
    bearing: bool = None # stationary location lacks bearing
    

    def destination_point(self, distance):
        '''Throws an error as StationaryGeographicLocation cannot move and lacks a bearing.'''
        raise RuntimeError('StationaryGeographicLocation lacks bearing and cannot move')


    def to_decimal_degrees(self):
        '''This method returns a (latitude, longitude, bearing) tuple with the location given in decimal degrees rather than radians.'''
        decimal_latitude = (self.latitude / pi) * 180.0
        decimal_longitude = (self.longitude / pi) * 180.0
        return decimal_latitude, decimal_longitude, decimal_bearing, self.bearing

    
