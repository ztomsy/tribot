from .stats_influx import TkgStatsInflux


class reporter:

    def __init__(self, server_id, exchange_id, session_uuid):

        self.session_uuid = session_uuid
        self.server_id = server_id
        self.exchange_id = exchange_id

        self.def_indicators = dict()  # definition indicators
        self.indicators = dict()

        self.def_indicators["server_id"] = self.server_id
        self.def_indicators["exchange_id"] = self.exchange_id
        self.def_indicators["session_uuid"] = self.session_uuid

    def set_indicator(self, key, value):
        self.indicators[key] = value

    def init_db(self, host, port, database, measurement, user="", password=""):

        self.influx = TkgStatsInflux(host,port, database, measurement)
        self.influx.set_tags(["server_id", "exchange_id", "session_uuid"])

    def push_to_influx(self):

        pass











