import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    os.makedirs('logs', exist_ok=True)

    handler = RotatingFileHandler(
        'logs/service.log',
        maxBytes=100000,
        backupCount=10
    )

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    handler.setFormatter(formatter)

    logging_level = getattr(logging, app.config['LOG_LEVEL'])
    handler.setLevel(logging_level)
    app.logger.setLevel(logging_level)
    app.logger.addHandler(handler)

    app.logger.info(
        f"The logger is configured. Logging level: {app.config['LOG_LEVEL']}")
