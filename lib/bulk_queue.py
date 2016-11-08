from threading import Timer


class BulkQueue():

    def __init__(self, es_client, threshold=10, flush_time=30):
        self.es_client = es_client
        self.threshold = threshold
        self.list = list()
        self.flush_time = flush_time
        self.time_thread = Timer(self.flush_time, self.flush)

    def start_timer(self):
        """ Start timer thread that flushes queue every X seconds """
        self.time_thread.start()

    def stop_timer(self):
        """ Stop timer thread """
        self.time_thread.cancel()

    def add(self, event):
        """ Add event to queue, flushing if we hit the threshold """
        self.list.append(event)
        if self.size() >= self.threshold:
            self.flush()

    def size(self):
        """ Size of the queue structure """
        return len(self.list)

    def flush(self):
        """ Write all stored events to ES """
        self.es_client.save_documents(self.list)
        self.list = list()
