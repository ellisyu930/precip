import logging.config
import yaml

# Define a function that loads the logging configuration file
def load_logging_config():
    with open('logging.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
    return config

# Load the logging configuration from file
config = load_logging_config()

# Configure the logging system
logging.config.dictConfig(config)

# Define a function that returns a logger object for the specified name
def get_logger(name: str):
    return logging.getLogger(name)