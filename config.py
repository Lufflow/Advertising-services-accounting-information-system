import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'some-secret-key-XD')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///flask.db')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 600,
    }

    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
