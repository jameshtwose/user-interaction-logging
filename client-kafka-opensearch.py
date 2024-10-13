import os
from opensearchpy import OpenSearch
import json
from confluent_kafka import Consumer
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

kafka_brokers = "localhost:29092"
kafka_topic = "canvas"
kafka_consumer = Consumer(
    {
        # For more info on these settings, see:
        # https://kafka.apache.org/documentation/#consumerconfigs
        # use a comma seperated str to add multiple brokers
        "bootstrap.servers": kafka_brokers,
        "group.id": "canvas_consumer",
        "auto.offset.reset": "latest",
        "socket.keepalive.enable": True,
    }
)
kafka_consumer.subscribe([kafka_topic])

def main() -> None:
    """
    an example showing how to create an synchronous connection to
    OpenSearch, create an index, index a document and search to
    return the document
    """
    host = "localhost"
    port = 9200
    auth = (
        "admin",
        os.getenv("OPENSEARCH_PASSWORD", "admin"),
    )  # For testing only. Don't store credentials in code.

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )

    info = client.info()
    print(f"Welcome to {info['version']['distribution']} {info['version']['number']}!")

    # create an index
    index_name = "canvas-index"
    index_body = {"settings": {"index": {"number_of_shards": 4}}}
    try:
        response = client.indices.create(index_name, body=index_body)
        print(response)
    except Exception as e:
        print(e)

    # add a document to the index

    # get latest document id
    query = {
        "size": 20,
        "query": {
            "match_all": {},
        },
        "sort": [
            {
                "_id": {
                    "order": "desc"
                }
            }
        ]
    }
    while True:
        # get latest document id
        response = client.search(body=query, index=index_name)
        if len(response["hits"]["hits"]) > 0:
            # print(response)
            doc_id = str(int(response["hits"]["hits"][0]["_id"]) + 1)
            print(doc_id)
        else:
            doc_id = "1"
        
        message = kafka_consumer.poll(1.0)
        print(message)
        if message is None:
            continue
        if message.error():
            logger.error(f"Consumer error: {message.error()}")
        logger.info(f"Received message: {message.value().decode('utf-8')}")
        
        document = eval(message.value().decode("utf-8"))
        # print(document)

        # index document
        response = client.index(index=index_name, body=document, id=doc_id, refresh=True)
        print(f"Indexed document: {response}")
    
    # document = {'timestamp': '2024-10-13T14:02:11.666913', 'message_type': 'basic-example', 'body': 'freedraw'}
    # doc_id = "3"
    # response = client.index(index=index_name, body=document, id=doc_id, refresh=True)
    # print(response)

if __name__ == "__main__":
    main()
