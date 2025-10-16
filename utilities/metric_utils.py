import time
import logging

def track_generation_metrics(func):
    """
    Decorator to track LLM generation performance
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logging.info(f"Generation completed in {duration:.2f} seconds")
            return result

        except Exception as e:
            logging.error(f"Generation failed: {str(e)}")
            raise

    return wrapper

def basic_logger(func):
    """
    Decorator to track activity
    """

    def wrapper(*args, **kwargs):

        try:
            result = func(*args, **kwargs)
            logging.info(f"Action: {result}")
            return result

        except Exception as e:
            logging.error(f"{func} failed: {str(e)}")
            raise

    return wrapper