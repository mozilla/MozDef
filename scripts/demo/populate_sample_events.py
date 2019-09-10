import glob
import os
import optparse
import random
import hjson
import time
from datetime import datetime

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


def handle_event(event):
    timestamp = toUTC(datetime.now()).isoformat()
    event['timestamp'] = timestamp
    event['receivedtimestamp'] = timestamp
    event['utctimestamp'] = timestamp

    # add demo to the tags so it's clear it's not real data.
    if 'tags' not in event:
        event['tags'] = list()
    event['tags'] += 'demodata'
    return event


def handle_events(sample_events, num_picked, es_client):
    selected_events = []
    if num_picked == 0:
        selected_events = sample_events
    else:
        # pick a random type of event to send
        for i in range(0, num_picked):
            selected_events.append(random.choice(sample_events))
    for event in selected_events:
        event = handle_event(event)
        es_client.save_event(event)


def run(num_rounds, num_events, sleep_time, es_client):
    sample_events_dir = os.path.join(os.path.dirname(__file__), "sample_events")
    sample_event_files = glob.glob(sample_events_dir + '/*')
    sample_events = []
    for sample_file in sample_event_files:
        sample_events += hjson.load(open(sample_file))
    # # pick a random number of events to send
    if num_rounds == 0:
        print("Running indefinitely")
        while True:
            handle_events(sample_events, num_events, es_client)
            time.sleep(sleep_time)
    else:
        print("Running for {0} rounds".format(num_rounds))
        handle_events(sample_events, num_events, es_client)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--elasticsearch_host', help='Elasticsearch host (default: http://localhost:9200)', default='http://localhost:9200')
    parser.add_option('--num_events', help='Number of random events to insert (default: 0 (run all))', default=0)
    parser.add_option('--num_rounds', help='Number of rounds to insert events (default: 0 (run continuously))', default=0)
    parser.add_option('--sleep_time', help='Number of seconds to sleep between rounds (default: 2)', default=2)
    options, arguments = parser.parse_args()
    es_client = ElasticsearchClient(options.elasticsearch_host)
    run(
        num_rounds=options.num_rounds,
        num_events=options.num_events,
        sleep_time=options.sleep_time,
        es_client=es_client
    )
