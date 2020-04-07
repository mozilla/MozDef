import time

from mozdef_util.bulk_queue import BulkQueue
from mozdef_util.query_models import SearchQuery, ExistsMatch

from tests.unit_test_suite import UnitTestSuite


class BulkQueueTest(UnitTestSuite):
    def setup(self):
        super().setup()

    def num_objects_saved(self):
        self.refresh(self.event_index_name)
        search_query = SearchQuery()
        search_query.add_must(ExistsMatch('keyname'))
        results = search_query.execute(self.es_client)
        return len(results['hits'])


class TestBasicInit(BulkQueueTest):

    def setup(self):
        super().setup()
        self.queue = BulkQueue(self.es_client)

    def test_threshold(self):
        assert self.queue.threshold == 10

    def test_size(self):
        assert self.queue.size() == 0

    def test_flush_time(self):
        assert self.queue.flush_time == 30


class TestInitWithThreshold(BulkQueueTest):

    def test_init_with_threshold(self):
        queue = BulkQueue(self.es_client, 100)
        assert queue.threshold == 100


class TestAdd(BulkQueueTest):

    def setup(self):
        super().setup()
        self.queue = BulkQueue(self.es_client, threshold=20)

    def test_basic_add(self):
        assert self.queue.size() == 0
        self.queue.add(index='events', body={'keyname', 'valuename'})
        assert self.queue.size() == 1
        assert self.queue.started() is False

    def test_add_exact_threshold(self):
        for num in range(0, 20):
            self.queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.queue.size() == 0
        assert self.num_objects_saved() == 20
        assert self.queue.started() is False

    def test_add_over_threshold(self):
        for num in range(0, 21):
            self.queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.num_objects_saved() == 20
        assert self.queue.size() == 1
        assert self.queue.started() is False

    def test_add_multiple_thresholds(self):
        for num in range(0, 201):
            self.queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.num_objects_saved() == 200
        assert self.queue.size() == 1
        assert self.queue.started() is False


class TestTimer(BulkQueueTest):

    def test_basic_timer(self):
        queue = BulkQueue(self.es_client, flush_time=2)
        assert queue.started() is False
        queue.start_thread()
        assert queue.started() is True
        queue.add(index='events', body={'keyname': 'valuename'})
        assert queue.size() == 1
        time.sleep(3)
        assert queue.size() == 0
        queue.stop_thread()
        assert queue.started() is False

    def test_over_threshold(self):
        queue = BulkQueue(self.es_client, flush_time=3, threshold=10)
        queue.start_thread()
        for num in range(0, 201):
            queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.num_objects_saved() == 200
        assert queue.size() == 1
        time.sleep(4)
        assert self.num_objects_saved() == 201
        assert queue.size() == 0
        queue.stop_thread()

    def test_two_iterations(self):
        queue = BulkQueue(self.es_client, flush_time=3, threshold=10)
        queue.start_thread()
        for num in range(0, 201):
            queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.num_objects_saved() == 200
        assert queue.size() == 1
        time.sleep(3)
        assert self.num_objects_saved() == 201
        assert queue.size() == 0
        for num in range(0, 201):
            queue.add(index='events', body={'keyname': 'value' + str(num)})
        assert self.num_objects_saved() == 401
        time.sleep(3)
        assert self.num_objects_saved() == 402
        queue.stop_thread()

    def test_ten_iterations(self):
        queue = BulkQueue(self.es_client, flush_time=3, threshold=10)
        queue.start_thread()
        total_events = 0
        for num_rounds in range(0, 10):
            for num in range(0, 20):
                total_events += 1
                queue.add(index='events', body={'keyname': 'value' + str(num)})
            assert self.num_objects_saved() == total_events
        assert queue.size() == 0
        queue.stop_thread()
        assert self.num_objects_saved() == 200
