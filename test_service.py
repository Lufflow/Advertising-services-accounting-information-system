import unittest
from datetime import datetime
from app import app, db, Service, Order


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

    def test_add_service_success(self):
        response = self.client.post('/add-service', data={
            'service_name': 'Реклама у блогера',
            'description': 'Рекламная интеграция',
            'price': 30000
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            service = Service.query.first()
            self.assertIsNotNone(service)
            self.assertEqual(service.service_name, 'Реклама у блогера')
            self.assertEqual(service.description, 'Рекламная интеграция')
            self.assertEqual(service.price, 30000)

    def test_add_service_empty_name(self):
        response = self.client.post('/add-service', data={
            'service_name': '',
            'description': 'Рекламная интеграция',
            'price': 30000
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Название услуги', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_add_service_empty_description(self):
        response = self.client.post('/add-service', data={
            'service_name': 'Реклама у блогера',
            'description': '',
            'price': 30000
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Описание услуги', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_add_service_empty_price(self):
        response = self.client.post('/add-service', data={
            'service_name': 'Реклама у блогера',
            'description': 'Рекламная интеграция',
            'price': ''
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Стоимость', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_update_service_success(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        response = self.client.post(f'/update-service/{service_id}', data={
            'service_name': 'Реклама у блогера',
            'description': 'Рекламная интеграция',
            'price': 30000
        })

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            update_service = db.session.get(Service, service_id)
            self.assertEqual(update_service.service_name, 'Реклама у блогера')
            self.assertEqual(update_service.description,
                             'Рекламная интеграция')
            self.assertEqual(update_service.price, 30000)

    def test_update_service_empty_name(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        response = self.client.post(f'/update-service/{service_id}', data={
            'service_name': '',
            'description': 'Рекламная интеграция',
            'price': 30000
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Название услуги', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_update_service_empty_description(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        response = self.client.post(f'/update-service/{service_id}', data={
            'service_name': 'Реклама у блогера',
            'description': '',
            'price': 30000
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Описание услуги', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_update_service_empty_price(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        response = self.client.post(f'/update-service/{service_id}', data={
            'service_name': 'Реклама у блогера',
            'description': 'Рекламная интеграция',
            'price': ''
        })

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Поле', response_text)
        self.assertIn('Стоимость', response_text)
        self.assertIn('обязательно для заполнения', response_text)

    def test_delete_service_success(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        response = self.client.get(
            f'/delete-service/{service_id}', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            deleted_service = db.session.get(Service, service_id)
            self.assertIsNone(deleted_service)

    def test_delete_customer_with_orders(self):
        with app.app_context():
            service = Service(
                service_name='Реклама у блогера',
                description='Рекламная интеграция',
                price=30000
            )
            db.session.add(service)
            db.session.commit()

            order = Order(
                customer_id=1,
                service_id=service.id,
                order_date=datetime.now().date(),
            )
            db.session.add(order)
            db.session.commit()

            service_id = service.id
            orders_count = Order.query.filter_by(
                service_id=service_id).count()

        response = self.client.get(
            f'/delete-service/{service_id}', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Невозможно удалить услугу. Есть оформленные заказы с этой услугой: {orders_count}".encode(
            'utf-8'), response.data)

        with app.app_context():
            service_still_exists = db.session.get(Service, service_id)
            self.assertIsNotNone(service_still_exists)


if __name__ == '__main__':
    unittest.main()
