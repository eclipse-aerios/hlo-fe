'''
    Docstring
'''
from app import app
from app import config
from app.utils.log import get_app_logger, check_log_path_exists

check_log_path_exists()
logger = get_app_logger()
logger.info('**HLO FE-EP engine started**')
logger.info("DEV_MODE: %s", config.DEV)
logger.info("CB URL: %s", config.CB_URL)
logger.info("CB PORT: %s", config.CB_PORT)
logger.info("REDPANDA BROKER: %s", config.producer_config['bootstrap.servers'])
logger.info("PRODUCER_TOPIC: %s", config.PRODUCER_TOPIC)
logger.info("TOKEN_URL: %s", config.TOKEN_URL)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
