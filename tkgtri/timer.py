from datetime import datetime
import time
import collections

class Timer:

    def __init__(self):
        self.start_time = datetime.now()
        self.notches = []

        self.bucket_size = 0
        self.tokens = 0
        self.bucket_seconds = 0

        self.now = datetime.now()
        self.request_time = self.now
        self.timestamp_before_request = datetime(1, 1, 1, 1, 1, 0)

        self.max_transactions_per_lap = int
        self.lap_time = int


    def notch(self, name):
        last = self.start_time if len(self.notches) == 0 else self.notches[-1]['time']
        self.notches.append({
            'name': name,
            'time': datetime.now(),
            'duration': (datetime.now() - last).total_seconds()
        })

    def check_timer(self):

        self.now = datetime.now()
        self.request_time = (self.now - self.timestamp_before_request).total_seconds()
        self.timestamp_before_request = self.now

        if 1 / self.request_time > self.max_transactions_per_lap / self.lap_time:
            print("Pause for:", self.lap_time / self.max_transactions_per_lap - self.request_time)
            time.sleep(self.lap_time / self.max_transactions_per_lap - self.request_time)
            self.timestamp_before_request = datetime.now()


    # TODO change to use map
    def results(self):
        result = []
        for n in self.notches:
            result.append('%s: %s s ' % (n['name'],  (n['duration'])))

        return '| '.join(result)

    def results_dict(self):
        d = collections.OrderedDict()
        for i in self.notches:
            d[i["name"]] = i["duration"]
        return d

    def reset_notches(self):
        self.notches = list()
