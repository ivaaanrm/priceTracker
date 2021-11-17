import logging 
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path,'price_tracker_logs.log')

#logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def do_logging(message):
    logger.info(message)

if __name__ == '__main__':
    do_logging()