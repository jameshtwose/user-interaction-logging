# user-interaction-logging
Demo of website interactions of users using streamlit for the frontend, Kafka to stream the logs, opensearch to index and search in the output, and a streamlit user interface to visualize trends.

- `docker exec -it kafka-0 bash`
- `cd /opt/bitnami/kafka/bin`
- `kafka-topics.sh --create --topic canvas --bootstrap-server localhost:9092`