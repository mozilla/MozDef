from .alerttask import AlertTask


class DeadmanAlertTask(AlertTask):

    def executeSearchEventsSimple(self):
        # We override this method to specify the size as 1
        # since we only care about if ANY events are found or not
        results = self.main_query.execute(self.es, indices=self.event_indices, size=1)
        return results
