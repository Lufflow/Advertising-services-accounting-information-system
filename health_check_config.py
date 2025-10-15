from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text


def check_db(app, db):
    try:
        db.session.execute(text("SELECT 1"))
        return 'OK'
    except SQLAlchemyError as e:
        app.logger.error(f"Health check - Database connection failed: {e}")
        return f"Fail: {str(e)}"
    except Exception as e:
        app.logger.error(f"Health check - Unexpected error: {e}")
        return f"Unexpected error: {str(e)}"


def check_logging(app):
    try:
        app.logger.info("Health check - Logging is available.")
        return 'OK'
    except Exception as e:
        app.logger.error(f"Health check - Logging failed: {e}")
        return f"Fail: ({str(e)})"
