import logging
import sys

def setup_logging():
    """Confingures structured JSON-like telemetry for observability"""
    logging.basicConfig(
        level=logging.INFO,
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose unformatted uvicorn webserver logs (optional for cleaner output)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
