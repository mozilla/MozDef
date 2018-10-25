from threading import Timer


class BulkQueue():

    def __init__(self, es_client, threshold=10, flush_time=30):
        self.es_client = es_client
        self.threshold = threshold
        self.list = list()
        self.flush_time = flush_time
        self.time_thread = Timer(self.flush_time, self.timer_over)
        self.running = False

    def timer_over(self):
        self.flush()
        self.time_thread = Timer(self.flush_time, self.timer_over)
        self.start_timer()

    def start_timer(self):
        """ Start timer thread that flushes queue every X seconds """
        self.time_thread.start()
        self.running = True

    def stop_timer(self):
        """ Stop timer thread """
        self.time_thread.cancel()
        self.running = False

    def started(self):
        return self.running

    def add(self, index, doc_type, body, doc_id=None):
        """ Add event to queue, flushing if we hit the threshold """
        bulk_doc = {
            "_index": index,
            "_type": doc_type,
            "_id": doc_id,
            "_source": body
        }
        self.list.append(bulk_doc)
        if self.size() >= self.threshold:
            self.flush()

    def size(self):
        """ Size of the queue structure """
        return len(self.list)

    def flush(self):
        """ Write all stored events to ES """
        self.es_client.save_documents(self.list)
        self.list = list()
