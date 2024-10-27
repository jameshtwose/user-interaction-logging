# user-interaction-logging
Demo of website interactions of users using streamlit for the frontend, Kafka to stream the logs, opensearch to index and search in the output, and a streamlit user interface to visualize trends.

### Setup (Docker - Kafka)
- `docker exec -it kafka-0 bash`
- `cd /opt/bitnami/kafka/bin`
- `kafka-topics.sh --create --topic canvas --bootstrap-server localhost:9092`

### Running
- `docker-compose up -d`
- `streamlit run app.py`
- `python client-kafka-opensearch.py`
- setup and run [LM Studio](https://lmstudio.ai/)
- `streamlit run dashboard.py`