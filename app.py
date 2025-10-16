from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from models import db, Customer, Service, Order
from logger_config import setup_logger
from health_check_config import check_db, check_logging
from validation import is_valid_phone, is_valid_date
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
app.secret_key = 'some-secret-key'
db.init_app(app)
setup_logger(app)
migrate = Migrate(app, db)


@app.route('/health')
def health_check():
    health_status = {
        'database': check_db(app=app, db=db),
        'logging': check_logging(app=app)
    }

    overall_check = all(value == 'OK' for value in health_status.values())
    status_code = 200 if overall_check else 500
    return jsonify(status='OK' if overall_check else 'FAIL', details=health_status), status_code


# <-- Базовый блок страницы
@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')
# Базовый блок страницы -->


# <-- Работа с клиентами
@app.route('/add-customer', methods=['POST', 'GET'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        company = request.form.get('company')

        if not name:
            flash('Поле "ФИО" обязательно для заполнения', 'danger')
            return render_template('add_customer.html', form_data=request.form)

        if not phone_number:
            flash('Поле "Номер телефона" обязательно для заполнения', 'danger')
            return render_template('add_customer.html', form_data=request.form)

        if not date_of_birth:
            flash('Поле "Дата рождения" обязательно для заполнения', 'danger')
            return render_template('add_customer.html', form_data=request.form)

        if not is_valid_phone(phone_number):
            flash(
                'Неверный формат номера телефона. Используйте российский формат', 'danger')
            return redirect(url_for('add_customer'))

        if not is_valid_date(date_of_birth):
            flash('Неверный формат даты. Введите корректную дату', 'danger')
            return redirect(url_for('add_customer'))

        existing_phone_number = Customer.query.filter_by(
            phone_number=phone_number).first()
        if existing_phone_number:
            flash('Клиент с таким номером телефона уже существует', 'danger')
            return render_template('add_customer.html', form_data=request.form)

        try:
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

            new_customer = Customer(
                name=name,
                date_of_birth=date_of_birth,
                phone_number=phone_number,
                email=email,
                company=company
            )

            db.session.add(new_customer)
            db.session.commit()
            flash('Клиент успешно добавлен!', 'success')
            return redirect(url_for('list_customers'))

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении клиента: {e}")
            flash('Произошла ошибка при добавлении клиента', 'danger')
            return redirect(url_for('add_customer'))

    return render_template('add_customer.html')


@app.route('/list-customers')
def list_customers():
    customers = Customer.query.all()
    return render_template('list_customers.html', customers=customers)


@app.route('/delete-customer/<int:customer_id>', methods=['GET'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)

        # Проверяем, есть ли связанные заказы
        orders_count = Order.query.filter_by(customer_id=customer_id).count()

        if orders_count > 0:
            flash(
                f'Невозможно удалить клиента. Существует {orders_count} связанных заказов.', 'warning')
            return redirect(url_for('list_customers'))

        db.session.delete(customer)
        db.session.commit()

        flash('Клиент успешно удален!', 'success')
        return redirect(url_for('list_customers'))

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении клиента: {e}")
        flash('Произошла ошибка при удалении клиента', 'danger')
        return redirect(url_for('list_customers'))


@app.route('/update-customer/<int:customer_id>', methods=['POST', 'GET'])
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        company = request.form.get('company')

        if not name:
            flash('Поле "ФИО" обязательно для заполнения', 'danger')
            return render_template('update_customer.html', customer=customer)

        if not phone_number:
            flash('Поле "Номер телефона" обязательно для заполнения', 'danger')
            return render_template('update_customer.html', customer=customer)

        if not date_of_birth:
            flash('Поле "Дата рождения" обязательно для заполнения', 'danger')
            return render_template('update_customer.html', customer=customer)

        if not is_valid_phone(phone_number):
            flash(
                'Неверный формат номера телефона. Используйте российский формат', 'danger')
            return redirect(url_for('add_customer'))

        if not is_valid_date(date_of_birth):
            flash('Неверный формат даты. Введите корректную дату', 'danger')
            return redirect(url_for('add_customer'))

        existing_phone_number = Customer.query.filter_by(
            phone_number=phone_number).first()
        if existing_phone_number:
            flash('Клиент с таким номером телефона уже существует', 'danger')
            return render_template('add_customer.html', form_data=request.form)

        try:
            date_obj = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

            customer.name = name
            customer.date_of_birth = date_obj
            customer.phone_number = phone_number
            customer.email = email
            customer.company = company

            db.session.commit()
            flash('Данные клиента успешно обновлены!', 'success')
            return redirect(url_for('list_customers'))

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при редактировании клиента: {e}")
            flash('Произошла ошибка при обновлении данных клиента', 'danger')

    return render_template('update_customer.html', customer=customer)
# Работа с клиентами -->


# <-- Работа с услугами
@app.route('/add-service', methods=['POST', 'GET'])
def add_service():
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        price = request.form.get('price')

        try:
            new_service = Service(
                service_name=service_name,
                description=description,
                price=price
            )

            db.session.add(new_service)
            db.session.commit()
            flash('Новая услуга успешно добавлена!', 'success')
            return redirect(url_for('list_services.html'))

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении новой услуги: {e}")
            flash('Произошла ошибка при добавлении новой услуги', 'danger')
            return redirect(url_for('add_service'))

    return render_template('add_service.html')


@app.route('/list-services')
def list_services():
    services = Service.query.all()
    return render_template('list_services.html', services=services)


@app.route('/delete-service/<int:service_id>', methods=['GET'])
def delete_service(service_id):
    try:
        service = Service.query.get_or_404(service_id)

        orders_count = Order.query.filter_by(service_id=service_id).count()

        if orders_count > 0:
            flash(
                f'Невозможно удалить услугу. Существует {orders_count} связанных заказов.', 'warning')
            return redirect(url_for('list_services'))

        db.session.delete(service)
        db.session.commit()

        flash('Услуга успешно удалена!', 'success')
        return redirect(url_for('list_services'))

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении услуги: {e}")
        flash('Произошла ошибка при удалении услуги', 'danger')
        return redirect(url_for('list_services'))


@app.route('/update-service/<int:service_id>', methods=['POST', 'GET'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':

        try:
            service.service_name = request.form.get('service_name')
            service.description = request.form.get('description')
            service.price = request.form.get('price')

            db.session.commit()
            flash('Данные услуги успешно обновлены!', 'success')
            return redirect(url_for('list_services'))

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при редактировании услуги: {e}")
            flash('Произошла ошибка при обновлении данных услуги', 'danger')

    return render_template('update_service.html', service=service)
# Работа с услугами -->


# <-- Работа с заказами
@app.route('/add-order', methods=['POST', 'GET'])
def add_order():
    customers = Customer.query.all()
    services = Service.query.all()

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')
        order_date = request.form.get('oder_date')

        try:
            order_date = datetime.now().date()

            new_order = Order(
                customer_id=customer_id,
                service_id=service_id,
                order_date=order_date
            )

            db.session.add(new_order)
            db.session.commit()

            flash('Заказ успешно оформлен', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при оформлении заказа: {e}")
            flash('Произошла ошибка при оформлении заказа', 'danger')
            return render_template('add_order.html', customers=customers, services=services)

    return render_template('add_order.html', customers=customers, services=services, now=datetime.now)


if __name__ == "__main__":
    app.run(debug=True)
