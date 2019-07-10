from threading import Thread, Lock
import time


class BulkQueue():

    def __init__(self, es_client, threshold=10, flush_time=30):
        self.es_client = es_client
        self.threshold = threshold
        self.list = list()
        self.flush_time = flush_time
        self.flush_thread = Thread(target=self.flush_periodically)
        self.flush_thread.daemon = True
        self.lock = Lock()
        self.running = False

    def start_thread(self):
        self.stopping_thread = False
        self.running = True
        self.flush_thread.start()

    def stop_thread(self):
        self.stopping_thread = True
        self.running = False

    def flush_periodically(self):
        while True and not self.stopping_thread:
            time.sleep(self.flush_time)
            self.flush()

    def started(self):
        return self.running

    def add(self, index, body, doc_id=None):
        """ Add event to queue, flushing if we hit the threshold """
        bulk_doc = {
            "_index": index,
            "_id": doc_id,
            "_source": body
        }
        self.lock.acquire()
        try:
            self.list.append(bulk_doc)
        finally:
            self.lock.release()
        if self.size() >= self.threshold:
            self.flush()

    def size(self):
        """ Size of the queue structure """
        return len(self.list)

    def flush(self):
        """ Write all stored events to ES """
        self.lock.acquire()
        try:
            self.es_client.save_documents(self.list)
            self.list = list()
        finally:
            self.lock.release()
