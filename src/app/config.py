'''
    Docstring
'''
import os

# Set DEV to False when building production container images
DEV = False
if DEV:
    # CB_URL = 'https://ncsrd-mvp-domain.aeriOS-project.eu'
    # CB_PORT = '443'
    # URL_VERSION = ''
    CB_URL = 'http://10.220.2.101'  # <=== node IP for node port
    CB_PORT = '31026' # <== exposed node port
    URL_VERSION = 'ngsi-ld/v1/'
    PRODUCER_TOPIC = 'fe2data_dev'
    K8S_SHIM_URL = 'http://localhost'
    K8S_SHIM_PORT = '5000'
else:
    CB_URL = os.environ.get('CB_URL')
    CB_PORT = os.environ.get('CB_PORT')
    URL_VERSION = 'ngsi-ld/v1/'
    PRODUCER_TOPIC = os.environ.get('PRODUCER_TOPIC')
    K8S_SHIM_URL = os.environ.get('K8S_SHIM_URL')
    K8S_SHIM_PORT = os.environ.get('K8S_SHIM_PORT')

TOKEN_URL = f"{K8S_SHIM_URL}:{K8S_SHIM_PORT}/token"

PARENT_PATH = os.path.dirname(__file__)
LOG_PATH = PARENT_PATH + '/log/fe.log'

# RedPanda Consumer configuration
producer_config = {
    'bootstrap.servers':
    os.environ.get('BOOTSTRAP_SERVERS',
                   'redpanda-0.redpanda.redpanda.svc.cluster.local:9093'),
    'client.id':
    'python-producer',
    'acks':
    'all',  # Ensures better data durability
    'retries':
    5,  # Number of retries if the message fails to send
    'retry.backoff.ms':
    300  # Interval between retries
    # 'group.id':
    # os.environ.get('GROUP_ID', 'python-consumer'),
    # 'auto.offset.reset':
    # os.environ.get('AUTO_OFFSET_RESET', 'earliest')
}

existing_services = {}
