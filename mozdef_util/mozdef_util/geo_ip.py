import geoip2.database


class GeoIP(object):
    def __init__(self, db_location):
        try:
            self.db = geoip2.database.Reader(db_location)
        except IOError:
            self.error = 'No Geolite DB Found!'

    def lookup_ip(self, ip):
        if hasattr(self, 'error'):
            return {'error': self.error}

        try:
            result = self.db.city(ip)
        except Exception as e:
            return {'error': str(e)}

        geo_dict = {}
        geo_dict['city'] = result.city.name
        geo_dict['continent'] = result.continent.code
        geo_dict['country_code'] = result.country.iso_code
        geo_dict['country_name'] = result.country.name
        geo_dict['dma_code'] = result.location.metro_code
        geo_dict['latitude'] = result.location.latitude
        geo_dict['longitude'] = result.location.longitude
        geo_dict['metro_code'] = ""
        if result.city.names:
            geo_dict['metro_code'] = result.city.names['en']
        geo_dict['postal_code'] = result.postal.code
        geo_dict['region_code'] = ""
        if result.subdivisions:
            geo_dict['region_code'] = result.subdivisions[0].iso_code
            geo_dict['metro_code'] += ', ' + result.subdivisions[0].iso_code
        geo_dict['time_zone'] = result.location.time_zone

        return geo_dict
