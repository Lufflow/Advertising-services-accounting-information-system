import unittest
from datetime import datetime
from app import app, db, Customer, Order


class TestCustomer(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_health_check(self):
        response = self.client.get('/health')
        response_data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['status'], 'OK')
        self.assertEqual(response_data['details']['database'], 'OK')
        self.assertEqual(response_data['details']['logging'], 'OK')

    def test_add_customer_success(self):
        response = self.client.post('/add-customer', data={
            'name': 'Иванов Иван Иванович', 'date_of_birth': '1990-01-01',
            'phone_number': '79001234567', 'email': 'tripleIVAN@mail.ru',
            'company': 'Ad Time!'
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            customer = Customer.query.first()
            self.assertIsNotNone(customer)
            self.assertEqual(customer.name, 'Иванов Иван Иванович')
            self.assertEqual(customer.phone_number, '79001234567')
            self.assertEqual(customer.email, 'tripleIVAN@mail.ru')
            self.assertEqual(customer.company, 'Ad Time!')

    def test_add_customer_empty_name(self):
        response = self.client.post('/add-customer', data={
            'name': '',
            'date_of_birth': '1990-01-01',
            'phone_number': '79001234567'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('ФИО', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_add_customer_empty_phone(self):
        response = self.client.post('/add-customer', data={
            'name': 'Иванов Иван Иванович',
            'date_of_birth': '1990-01-01',
            'phone_number': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Номер телефона', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_add_customer_invalid_phone(self):
        response = self.client.post('/add-customer', data={
            'name': 'Иван Иванов',
            'date_of_birth': '1990-01-01',
            'phone_number': '123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Неверный формат номера телефона. Используйте российский формат".encode(
            'utf-8'), response.data)

    def test_add_customer_invalid_date(self):
        response = self.client.post('/add-customer', data={
            'name': 'Иван Иванов',
            'date_of_birth': '2100-01-01',
            'phone_number': '79001234567'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Дата рождения не может быть в будущем".encode(
            'utf-8'), response.data)

    def test_add_customer_existing_phone(self):
        with app.app_context():
            existing_customer = Customer(
                name='Петров Петр Петрович',
                date_of_birth=datetime.strptime(
                    '1985-05-05', '%Y-%m-%d').date(),
                phone_number='79001234567'
            )
            db.session.add(existing_customer)
            db.session.commit()

        response = self.client.post('/add-customer', data={
            'name': 'Иванов Иван Иванович',
            'date_of_birth': '1990-01-01',
            'phone_number': '79001234567'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Клиент с таким номером телефона уже существует".encode('utf-8'), response.data)

    def test_update_customer_success(self):
        with app.app_context():
            customer = Customer(
                name='Иванов Иван Иванович',
                date_of_birth=datetime.strptime(
                    '1990-01-01', '%Y-%m-%d').date(),
                phone_number='79001234567'
            )
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id

        response = self.client.post(f'/update-customer/{customer_id}', data={
            'name': 'Иванов Иван Петрович',
            'date_of_birth': '1991-02-02',
            'phone_number': '79007654321'
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            updated_customer = db.session.get(Customer, customer_id)
            self.assertEqual(updated_customer.name, 'Иванов Иван Петрович')
            self.assertEqual(updated_customer.phone_number, '79007654321')

    def test_update_customer_existing_phone(self):
        with app.app_context():
            customer1 = Customer(
                name='Иванов Иван Иванович',
                date_of_birth=datetime.strptime(
                    '1990-01-01', '%Y-%m-%d').date(),
                phone_number='79001234567'
            )
            customer2 = Customer(
                name='Петров Петр Петрович',
                date_of_birth=datetime.strptime(
                    '1985-05-05', '%Y-%m-%d').date(),
                phone_number='79007654321'
            )
            db.session.add(customer1)
            db.session.add(customer2)
            db.session.commit()
            customer1_id = customer1.id

        response = self.client.post(f'/update-customer/{customer1_id}', data={
            'name': 'Иванов Иван Иванович',
            'date_of_birth': '1990-01-01',
            'phone_number': '79007654321'  # Номер П.П.Петрова
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Клиент с таким номером телефона уже существует".encode('utf-8'), response.data)

    def test_delete_customer_success(self):
        with app.app_context():
            customer = Customer(
                name='Иванов Иван Иванович',
                date_of_birth=datetime.strptime(
                    '1990-01-01', '%Y-%m-%d').date(),
                phone_number='79001234567'
            )
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id

        response = self.client.get(
            f'/delete-customer/{customer_id}', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            deleted_customer = db.session.get(Customer, customer_id)
            self.assertIsNone(deleted_customer)

    def test_delete_customer_with_orders(self):
        with app.app_context():
            customer = Customer(
                name='Иванов Иван Иванович',
                date_of_birth=datetime.strptime(
                    '1990-01-01', '%Y-%m-%d').date(),
                phone_number='79001234567'
            )
            db.session.add(customer)
            db.session.commit()

            order = Order(
                customer_id=customer.id,
                service_id=1,
                order_date=datetime.now().date(),
            )
            db.session.add(order)
            db.session.commit()

            customer_id = customer.id
            orders_count = Order.query.filter_by(
                customer_id=customer_id).count()

        response = self.client.get(
            f'/delete-customer/{customer_id}', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Невозможно удалить клиента. У этого клиента есть оформленные заказы: {orders_count}".encode(
            'utf-8'), response.data)

        with app.app_context():
            customer_still_exists = db.session.get(Customer, customer_id)
            self.assertIsNotNone(customer_still_exists)


if __name__ == '__main__':
    unittest.main()
