import unittest
from datetime import datetime, timedelta
from app import app, db, Order


class TestService(unittest.TestCase):

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

    def test_add_order_success(self):
        response = self.client.post('/add-order', data={
            'customer_id': 1,
            'service_id': 1,
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            order = Order.query.first()
            self.assertIsNotNone(order)
            self.assertEqual(order.customer_id, 1)
            self.assertEqual(order.service_id, 1)
            self.assertEqual(order.order_date, datetime.now().date())

    def test_add_order_empty_customer(self):
        response = self.client.post('/add-order', data={
            'customer_id': '',
            'service_id': 1,
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите клиента", response_text)

    def test_add_order_empty_service(self):
        response = self.client.post('/add-order', data={
            'customer_id': 1,
            'service_id': '',
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите услугу", response_text)

    def test_add_order_invalid_future_date(self):
        future_date = datetime.now().date() + timedelta(days=1)
        response = self.client.post('/add-order', data={
            'customer_id': 1,
            'service_id': 1,
            'order_date': future_date.strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Дата заказа не может быть в будущем", response_text)

    def test_add_order_invalid_format_date(self):
        response = self.client.post('/add-order', data={
            'customer_id': 1,
            'service_id': 1,
            'order_date': datetime.now().date().strftime('%d-%y-%M')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Некорректный формат даты", response_text)

    def test_update_order_success(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': 2,
            'service_id': 2,
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            update_order = db.session.get(Order, order_id)
            self.assertEqual(update_order.customer_id, 2)
            self.assertEqual(update_order.service_id, 2)
            self.assertEqual(update_order.order_date, datetime.now().date())

    def test_update_order_empty_customer(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': '',
            'service_id': 1,
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите клиента", response_text)

    def test_update_order_empty_service(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': 1,
            'service_id': '',
            'order_date': datetime.now().date()
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Пожалуйста, выберите услугу", response_text)

    def test_update_order_invalid_future_date(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        future_date = datetime.now().date() + timedelta(days=1)
        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': 1,
            'service_id': 1,
            'order_date': future_date.strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Дата заказа не может быть в будущем", response_text)

    def test_update_order_invalid_format_date(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
                order_date=datetime.now().date()
            )
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = self.client.post(f'/update-order/{order_id}', data={
            'customer_id': 1,
            'service_id': 1,
            'order_date': datetime.now().date().strftime('%d-%y-%M')
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn("Некорректный формат даты", response_text)

    def test_delete_order_success(self):
        with app.app_context():
            order = Order(
                customer_id=1,
                service_id=1,
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
