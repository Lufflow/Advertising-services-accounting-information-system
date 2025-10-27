import unittest
from datetime import datetime, timedelta
from app import app, db, Order, Customer, Service


class TestService(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            self.create_test_data()

    def create_test_data(self):
        customer1 = Customer(
            name="Иванов Иван Иванович",
            phone_number="+79500000001",
            date_of_birth=datetime(1990, 1, 1).date()
        )
        customer2 = Customer(
            name="Петр Петров",
            phone_number="+79500000002",
            date_of_birth=datetime(1985, 5, 15).date()
        )

        service1 = Service(
            service_name="Реклама в соцсетях",
            description="Продвижение в социальных сетях",
            price=5000
        )
        service2 = Service(
            service_name="Контекстная реклама",
            description="Реклама в поисковых системах",
            price=10000
        )

        db.session.add_all([customer1, customer2, service1, service2])
        db.session.commit()

        self.customer1_id = customer1.id
        self.customer2_id = customer2.id
        self.service1_id = service1.id
        self.service2_id = service2.id

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

    def test_add_order_success(self):
        response = self.client.post('/add-order', data={
            'customer_id': str(self.customer1_id),
            'service_id': str(self.service1_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            order = Order.query.first()
            self.assertIsNotNone(order)
            self.assertEqual(order.customer_id, self.customer1_id)
            self.assertEqual(order.service_id, self.service1_id)
            self.assertEqual(order.order_date, datetime.now().date())

    def test_add_order_empty_customer(self):
        response = self.client.post('/add-order', data={
            'customer_id': '',
            'service_id': str(self.service1_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите клиента", response_text)

    def test_add_order_empty_service(self):
        response = self.client.post('/add-order', data={
            'customer_id': str(self.customer1_id),
            'service_id': '',
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите услугу", response_text)

    def test_add_order_with_nonexistent_customer(self):
        response = self.client.post('/add-order', data={
            'customer_id': '99999',
            'service_id': str(self.service1_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn(
            "Выбранный клиент не существует в базе данных", response_text)

    def test_add_order_with_nonexistent_service(self):
        response = self.client.post('/add-order', data={
            'customer_id': str(self.customer1_id),
            'service_id': '99999',
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn(
            "Выбранная услуга не существует в базе данных", response_text)

    def test_add_order_invalid_future_date(self):
        future_date = datetime.now().date() + timedelta(days=1)
        response = self.client.post('/add-order', data={
            'customer_id': str(self.customer1_id),
            'service_id': str(self.service1_id),
            'order_date': future_date.strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Дата заказа не может быть в будущем", response_text)

    def test_add_order_invalid_format_date(self):
        response = self.client.post('/add-order', data={
            'customer_id': str(self.customer1_id),
            'service_id': str(self.service1_id),
            'order_date': 'invalid-date-format'
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Некорректный формат даты", response_text)

    def test_update_order_success(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': str(self.customer2_id),
            'service_id': str(self.service2_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            update_order = db.session.get(Order, order_id)
            self.assertEqual(update_order.customer_id, self.customer2_id)
            self.assertEqual(update_order.service_id, self.service2_id)
            self.assertEqual(update_order.order_date, datetime.now().date())

    def test_update_order_empty_customer(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': '',
            'service_id': str(self.service1_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите клиента", response_text)

    def test_update_order_empty_service(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': str(self.customer1_id),
            'service_id': '',
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите услугу", response_text)

    def test_update_order_with_nonexistent_customer(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': '99999',
            'service_id': str(self.service1_id),
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn(
            "Выбранный клиент не существует в базе данных", response_text)

    def test_update_order_with_nonexistent_service(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id
        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': str(self.customer1_id),
            'service_id': '99999',
            'order_date': datetime.now().date().strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn(
            "Выбранная услуга не существует в базе данных", response_text)

    def test_update_order_invalid_future_date(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        future_date = datetime.now().date() + timedelta(days=1)
        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': str(self.customer1_id),
            'service_id': str(self.service1_id),
            'order_date': future_date.strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Дата заказа не может быть в будущем", response_text)

    def test_update_order_invalid_format_date(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': str(self.customer1_id),
            'service_id': str(self.service1_id),
            'order_date': 'invalid-date-format'
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Некорректный формат даты", response_text)

    def test_delete_order_success(self):
        with app.app_context():
            order = Order(
                customer_id=self.customer1_id,
                service_id=self.service1_id,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.get(
            f'/delete-order/{order_id}', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            deleted_order = db.session.get(Order, order_id)
            self.assertIsNone(deleted_order)


if __name__ == '__main__':
    unittest.main()
