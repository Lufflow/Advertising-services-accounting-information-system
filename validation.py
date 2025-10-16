import re
from datetime import datetime, date


def is_valid_phone(phone):
    pattern = r'^(\+7|7|8)?[489][0-9]{9}$'
    phone_clean = re.sub(r'[^\d+]', '', phone)
    return re.match(pattern, phone_clean) is not None


def is_valid_date(date_str):
    try:
        birth_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()

        if birth_date > today:
            return False, "Дата рождения не может быть в будущем"

        age = today.year - birth_date.year

        if today < birth_date.replace(year=today.year):
            age -= 1

        return age >= 18, "Клиент должен быть совершеннолетним (18 лет)"

    except ValueError:
        return False
