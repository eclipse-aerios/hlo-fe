'''
    Protobuf and kafka related functions
'''
from confluent_kafka import Producer, KafkaException
from app.config import PRODUCER_TOPIC, producer_config
from app.utils.log import get_app_logger
from app.app_models.py_files import front_end_pb2

logger = get_app_logger()

def create_fe2data_output(service_id):
    '''
        Create protobuf message for kafka towards  HLO_DATA_AGGREGATOR
    '''
    message = front_end_pb2.HLODataAggregatorOutput()
    message.service.id = service_id
    return message

def serialize_to_bytes(feinput):
    '''
        Binary Serialize string to be sent to kafka as protobuf message
    '''
    return feinput.SerializeToString()

# def parse_from_bytes(data):
#     '''
#         Parse received kafka protobuf message from binary to string
#     '''
#     feinput = aggregator.HLOFEInput()
#     feinput.ParseFromString(data)
#     return feinput


def on_delivery(err, msg):
    '''
     Callback for kafka delivering message
    '''
    if err is not None:
        logger.error('Delivery failed: %s', err)
    else:
        logger.info('Message delivered to %s [%s]', msg.topic(), msg.partition())


def produce_message(service_id):
    '''
    Deliver message to redpanda
    '''
    producer = Producer(producer_config)
    # Create protobuf message for redpanda
    # According to protobuf service data model
    # And (binary) serialize it
    protobuf_msg = serialize_to_bytes(
        create_fe2data_output(service_id=service_id))
    logger.info('Protobuf message: %s', protobuf_msg)

    try:
        # Sending a message to the topic
        producer.produce(topic=PRODUCER_TOPIC,
                         value=protobuf_msg,
                         callback=on_delivery)

        # Wait for delivery confirmation
        producer.poll(5)

    except KafkaException as e:
        logger.error('Kafka Error: %s', e)

    finally:
        # Close the producer
        producer.flush()

if __name__ == "__main__":
    produce_message('urn:ngsi-ld:service:fake')
