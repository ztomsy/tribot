from datetime import datetime


class Timer:

    def __init__(self):
        self.start_time = datetime.now()
        self.notches = []

    def notch(self, name):
        last = self.start_time if len(self.notches) == 0 else self.notches[-1]['time']
        self.notches.append({
            'name': name,
            'time': datetime.now(),
            'duration': (datetime.now() - last).total_seconds()
        })

    # TODO change to use map
    def results(self):
        result = []
        for n in self.notches:
            result.append('%s: %s ms ' % (n['name'],  (n['duration'].microseconds / 1000)))

        return '| '.join(result)
