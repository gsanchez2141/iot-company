import logging
import json
from pg8000 import connect, Cursor
from typing import List

from iot_company.repository.model.iot_model import MessageDTO, MessagesBatchDTO
# Configure logging to send messages to CloudWatch Logs
logging.basicConfig(level=logging.INFO)

# Retrieve PostgreSQL connection parameters from environment variables
db_host = 'my_postgres'#'localhost' # 'my_postgres'
db_port = 5432
db_name = 'mydatabase'
db_user = 'myuser'
db_password = 'mypassword'

def connect_to_postgres():
    try:
        conn = connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        return conn
    except Exception as e:
        logging.error(f"Error creating PostgreSQL connection: {e}")
        raise  # Re-raise the exception

def process_sqs_record(record):
    try:
        message_dto = MessageDTO.model_validate(record['body'])
        print(f"Processing message: {message_dto}")
        return (
            message_dto.region,
            message_dto.origin_coord,
            message_dto.destination_coord,
            message_dto.datetime,
            message_dto.datasource
        )
    except Exception as e:
        print(f"Error processing message: {e}")
        return None


# def write_to_postgres(cursor: Cursor, messages):
#     insert_query = "INSERT INTO iot (region, origin_coord, destination_coord, datetime, datasource) VALUES (%s, %s, %s, %s, %s)"
#     logging.info(f'SQL Query: {insert_query}')
#     logging.info(f'Values: {messages}')
#
#     for message in messages:
#         cursor.execute(insert_query, message)
#
#     logging.info('Persisted with success')


def write_to_postgres(cursor: Cursor, messages: List[tuple]):
    insert_query = "INSERT INTO iot (region, origin_coord, destination_coord, datetime, datasource) VALUES (%s, %s, %s, %s, %s)"
    logging.info(f'SQL Query: {insert_query}')

    # Use executemany for batch insert
    cursor.executemany(insert_query, messages)

    logging.info('Persisted with success')


def process_batches(messages_to_insert, batch_size):
    batch_count = 0  # Initialize batch count

    with connect_to_postgres() as conn:
        cursor = conn.cursor()
        try:
            for batch in chunks(messages_to_insert, batch_size):
                logging.info('Writing batch')
                logging.info(f'Writing batch {batch_count}')  # Log batch count

                write_to_postgres(cursor, batch)
                conn.commit()
                batch_count += 1  # Increment batch count

        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            cursor.close()

def lambda_handler(event, context):
    logging.info('Hello from Lambda!')
    logging.info('Event: %s', event)

    try:
        messages_batch_dto = MessagesBatchDTO.model_validate(
            {'messages': [json.loads(record['body']) for record in event['Records']]})

        if messages_batch_dto:
            messages_to_insert = [
                (
                    message.region,
                    message.origin_coord,
                    message.destination_coord,
                    message.datetime,
                    message.datasource
                )
                for message in messages_batch_dto.messages
            ]

            logging.info('Messages Batch DTO')

            # Write messages to PostgreSQL in batches
            batch_size = 500
            process_batches(messages_to_insert, batch_size)
            logging.info('Finished writing')

    except Exception as e:
        logging.error(f"Error processing messages batch: {e}")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

if __name__ == "__main__":
    event_stream = None
    # Streaming SQS Trigger
    with open('../events/batch_sqs_to_lambda_event.json', 'r') as file:
        event_stream = file.read()

    lambda_handler(json.loads(event_stream), "")
