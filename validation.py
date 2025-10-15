import re
from datetime import datetime


def is_valid_phone(phone):
    pattern = r'^(\+7|7|8)?[489][0-9]{9}$'
    phone_clean = re.sub(r'[^\d+]', '', phone)
    return re.match(pattern, phone_clean) is not None


def is_valid_date(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date <= datetime.now().date()
    except ValueError:
        return False
