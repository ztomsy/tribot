from influxdb import InfluxDBClient


class TkgStatsInflux:

    def __init__(self, host, port, database, measurement):

        self.host = host  # "13.231.173.161"
        self.port = port  # 8086
        self.database = database  # "tkg_dev"

        self.measurement = measurement  # "tri_deals_results"

        self.client = InfluxDBClient(host=self.host, port=self.port, database=self.database)

        self.tags = list()  # list of tags from the deal info dict

    def set_tags(self, tags: list):
        self.tags = tags

    def extract_tags_and_fields(self, deal_row:dict):
        tags = dict()
        fields = dict()

        for i in deal_row:
            if i in self.tags:
                tags[i] = deal_row[i]
            else:
                fields[i] = deal_row[i]

        return {"tags": tags, "fields": fields}

    def write_deal_info(self, deal_row:dict):

        updtmsg = dict()

        updtmsg["measurement"] = self.measurement

        stats_data = self.extract_tags_and_fields(deal_row)

        updtmsg["tags"] = stats_data["tags"]
        updtmsg["fields"] = stats_data["fields"]

        self.client.write_points([updtmsg])
