import boto3
import json
import uuid
from datetime import datetime
from faker import Faker
from shapely.geometry import Point
from shapely.wkt import dumps as wkt_dumps
import random
import threading
import logging
from queue import Queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'your-queue-url' with the actual URL of your SQS queue
queue_url = 'http://sqs.us-west-2.localhost.localstack.cloud:4566/000000000000/my-queue'

# Define the total number of messages and number of threads
TOTAL_MESSAGES = 10000
NUM_THREADS = 4
BATCH_SIZE = 10

fake = Faker()

# Shared queue for coordinating messages
message_queue = Queue()


def generate_sample_payload():
    region = fake.city()
    origin_coord = generate_random_point()
    destination_coord = generate_random_point()
    datetime_str = fake.date_time_this_decade().isoformat()
    datasource = fake.word()

    return {
        "region": region,
        "origin_coord": origin_coord,
        "destination_coord": destination_coord,
        "datetime": datetime_str,
        "datasource": datasource
    }


def generate_random_point():
    # Generate random coordinates within a specific bounding box
    min_longitude, max_longitude = -180, 180
    min_latitude, max_latitude = -90, 90

    longitude = random.uniform(min_longitude, max_longitude)
    latitude = random.uniform(min_latitude, max_latitude)

    # Create a Shapely Point object and convert it to WKT format
    point = Point(longitude, latitude)
    return wkt_dumps(point)


def send_messages_to_sqs(messages):
    # Create an SQS client
    sqs = boto3.client('sqs', region_name='us-west-2', endpoint_url='http://localhost:4566')

    # Convert messages to JSON
    message_bodies = [json.dumps(payload) for payload in messages]

    # Send messages in batches
    sent_total_count = 0
    for i in range(0, len(message_bodies), BATCH_SIZE):
        batch = message_bodies[i:i + BATCH_SIZE]
        entries = [{'Id': str(idx), 'MessageBody': body} for idx, body in enumerate(batch)]

        response = sqs.send_message_batch(QueueUrl=queue_url, Entries=entries)

        # Log every 100 messages sent to SQS
        sent_count = 0
        for success in response.get('Successful', []):
            sent_count += 1
            if sent_count == 10:
                sent_total_count += sent_count
                logger.info(f"Thread {threading.current_thread().name} sent {sent_total_count} messages to SQS")
            # logger.info(f"Thread {threading.current_thread().name} sent MessageId: {success['MessageId']}")
            # logger.info(f"Thread {threading.current_thread().name} sent {sent_count} messages to SQS")
            # if sent_count % 100 == 0:
                # logger.info(f"Thread {threading.current_thread().name} sent {sent_count} messages to SQS")


def worker():
    # Each thread generates and enqueues messages
    for _ in range(TOTAL_MESSAGES // NUM_THREADS):
        sample_payload = generate_sample_payload()
        message_queue.put(sample_payload)

        # Log every 100 messages processed by each thread
        if message_queue.qsize() % 100 == 0:
            logger.info(f"Thread {threading.current_thread().name} processed {message_queue.qsize()} messages")


def main():
    # Create and start threads
    threads = []
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=worker, name=f"Thread-{i + 1}")
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Accumulate messages from the queue
    messages_to_send = [message_queue.get() for _ in range(message_queue.qsize())]

    # Send messages
    send_messages_to_sqs(messages_to_send)

    logger.info("All threads have finished processing messages")


if __name__ == "__main__":
    main()
