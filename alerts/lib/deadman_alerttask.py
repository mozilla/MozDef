from alerttask import AlertTask


class DeadmanAlertTask(AlertTask):
    def __init__(self):
        self.deadman = True

    def executeSearchEventsSimple(self):
        # We override this method to specify the size as 1
        # since we only care about if ANY events are found or not
        return self.main_query.execute(self.es, indices=self.event_indices, size=1)
