import re
from datetime import datetime, date


def is_valid_phone(phone):
    pattern = r'^(\+7|7|8)?[489][0-9]{9}$'
    phone_clean = re.sub(r'[^\d+]', '', phone)
    return re.match(pattern, phone_clean) is not None


class ValidDate:
    @staticmethod
    def is_valid_birth_date(date_str):

        if not date_str or not date_str.strip():
            return False, "Поле \"Дата рождения\" обязательно для заполнения"

        try:
            birth_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            impossible_date = datetime.strptime(
                '1905-01-01', '%Y-%m-%d').date()

            if birth_date > today:
                return False, "Дата рождения не может быть в будущем"

            if birth_date < impossible_date:
                return False, "Недопустимая дата рождения (позднее 1905г.)"

            age = today.year - birth_date.year

            if today < birth_date.replace(year=today.year):
                age -= 1

            return age >= 18, "Клиент должен быть совершеннолетним (18 лет)"

        except ValueError:
            return False, "Некорректный формат даты"

    @staticmethod
    def is_valid_order_date(date_str):
        try:
            if date_str is None or str(date_str).strip() == '':
                return True, ''

            order_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
            today = datetime.now().date()

            if order_date > today:
                return False, "Дата заказа не может быть в будущем"

            return True, ''

        except ValueError:
            return False, "Некорректный формат даты"
        except Exception as e:
            return False, f"Ошибка при обработке даты: {str(e)}"


def is_empty_field(data):
    return data is None or data == '' or data == '---'
