from confluent_kafka import Producer
import logging
import random
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def kafka_producer(
    kafka_topic: str = "canvas",
    kafka_brokers: str = "localhost:29092",
    request_dict: dict = {
        "timestamp": datetime.datetime.now().isoformat(),
        "message_type": "example",
        "body": "example",
    },
):
    p = Producer(
        {
            # For more info on these settings, see:
            # https://kafka.apache.org/documentation/#producerconfigs
            # use a comma seperated str to add multiple brokers
            "bootstrap.servers": kafka_brokers,
            "socket.keepalive.enable": True,
        }
    )

    p.produce(kafka_topic, str(request_dict))
    p.poll(1)
    p.flush()
    logger.info(f"Sent message: {request_dict}")
    return request_dict