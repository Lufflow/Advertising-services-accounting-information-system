from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from models import db, Customer, Service, Order
from config import Config
from logger_config import setup_logger
from health_check_config import check_db, check_logging
from validation import is_valid_phone, ValidDate, is_empty_field
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
setup_logger(app)
db.init_app(app)
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
def index():
    return render_template('index.html')
# Базовый блок страницы -->


# <-- Работа с клиентами
@app.route('/add-customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        company = request.form.get('company')

        app.logger.info(
            f"Start creating customer")

        if is_empty_field(name):
            app.logger.warning(
                f"Attempt to create a customer with an empty name field.")
            flash("Поле \"ФИО\" обязательно для заполнения", 'danger')
            return render_template('add_customer.html', form_data=request.form)

        if is_empty_field(phone_number):
            app.logger.warning(
                f"Attempt to create a customer with an empty phone number field.")
            flash("Поле \"Номер телефона\" обязательно для заполнения", 'danger')
            return render_template('add_customer.html', form_data=request.form)

        if not is_valid_phone(phone_number):
            app.logger.warning(
                f"Attempt to create a client with an invalid phone number format.")
            flash(
                "Неверный формат номера телефона. Используйте российский формат", 'danger')
            return render_template('add_customer.html', form_data=request.form)

        is_valid, message = ValidDate.is_valid_birth_date(date_of_birth)
        if not is_valid:
            app.logger.warning(
                f"Attempt to create a client with an invalid date of birth. Message: {message}")
            flash(message, 'danger')
            return render_template('add_customer.html', form_data=request.form)

        existing_phone_number = Customer.query.filter_by(
            phone_number=phone_number).first()
        if existing_phone_number:
            app.logger.warning(
                f"Attempt to create a client with an existing phone number in the database. Phone number: {phone_number}")
            flash("Клиент с таким номером телефона уже существует", 'danger')
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

            app.logger.info(
                f"Service successfully created. ID: {new_customer.id}")

            flash("Клиент успешно добавлен!", 'success')
            return redirect(url_for('list_customers'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Error creating service. ID: {new_customer.id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при добавлении клиента: {e}")
            flash("Произошла ошибка при добавлении клиента", 'danger')
            return render_template('add_customer.html', form_data=request.form)

    app.logger.info("The new customer creation page has loaded")

    return render_template('add_customer.html')


@app.route('/update-customer/<int:customer_id>', methods=['GET', 'POST'])
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        company = request.form.get('company')

        app.logger.info(
            f"Start editing customer. ID: {customer_id}.")

        if is_empty_field(name):
            app.logger.warning(
                f"Attempt to send an customer with an empty customer name field. ID: {customer_id}.")
            flash("Поле \"ФИО\" обязательно для заполнения", 'danger')
            return render_template('update_customer.html', customer=customer)

        if is_empty_field(phone_number):
            app.logger.warning(
                f"Attempt to send an customer with an empty customer phone number field. ID: {customer_id}.")
            flash("Поле \"Номер телефона\" обязательно для заполнения", 'danger')
            return render_template('update_customer.html', customer=customer)

        if not is_valid_phone(phone_number):
            app.logger.warning(
                f"Attempt to send a customer with an invalid phone number format.")
            flash(
                "Неверный формат номера телефона. Используйте российский формат", 'danger')
            return render_template('update_customer.html', customer=customer)

        is_valid, message = ValidDate.is_valid_birth_date(date_of_birth)
        if not is_valid:
            app.logger.warning(
                f"Attempt to send a customer with an invalid date of birth. Message: {message}")
            flash(message, 'danger')
            return render_template('update_customer.html', customer=customer)

        existing_phone_number = Customer.query.filter(
            Customer.phone_number == phone_number,
            Customer.id != customer_id
        ).first()

        if existing_phone_number:
            app.logger.warning(
                f"Attempt to send a customer with an existing phone number in the database. Phone number: {phone_number}")
            flash("Клиент с таким номером телефона уже существует", 'danger')
            return render_template('update_customer.html', form_data=request.form)

        try:
            date_obj = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

            customer.name = name
            customer.date_of_birth = date_obj
            customer.phone_number = phone_number
            customer.email = email
            customer.company = company

            db.session.commit()

            app.logger.info(
                f"Customer successfully updated. ID: {customer_id}.")

            flash("Данные клиента успешно обновлены!", 'success')
            return redirect(url_for('list_customers'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Customer modification error. ID: {customer_id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при редактировании клиента: {e}")
            flash("Произошла ошибка при обновлении данных клиента", 'danger')

    app.logger.info("Customer edit page loaded")

    return render_template('update_customer.html', customer=customer)


@app.route('/delete-customer/<int:customer_id>', methods=['GET', 'POST'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)

        orders_count = Order.query.filter_by(customer_id=customer_id).count()

        if orders_count > 0:
            app.logger.warning(
                f"Attempt to delete a customer associated with an order(s). ID: {customer.id}, Number of orders: {orders_count}.")
            flash(
                f"Невозможно удалить клиента. У этого клиента есть оформленные заказы: {orders_count}", 'warning')
            return redirect(url_for('list_customers'))

        db.session.delete(customer)
        db.session.commit()

        app.logger.info(
            f"Service successfully deleted. ID: {customer.id}.")

        flash("Клиент успешно удален!", 'success')
        return redirect(url_for('list_customers'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Error deleting service. ID: {customer.id}. Error: {str(e)}", exc_info=True)
        print(f"Ошибка при удалении клиента: {e}")
        flash("Произошла ошибка при удалении клиента", 'danger')
        return redirect(url_for('list_customers'))


@app.route('/list-customers')
def list_customers():
    customers = Customer.query.all()
    app.logger.info("The page with the list of all clients has been loaded")
    return render_template('list_customers.html', customers=customers)
# Работа с клиентами -->


# <-- Работа с услугами
@app.route('/add-service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        price = request.form.get('price')

        app.logger.info(
            f"Start creating service")

        if is_empty_field(service_name):
            app.logger.warning(
                f"Attempt to create a service with an empty service name field.")
            flash("Поле \"Название услуги\" обязательно для заполнения", 'danger')
            return render_template('add_service.html', form_data=request.form)

        if is_empty_field(description):
            app.logger.warning(
                f"Attempt to create a service with an empty service description field.")
            flash("Поле \"Описание услуги\" обязательно для заполнения", 'danger')
            return render_template('add_service.html', form_data=request.form)

        if is_empty_field(price):
            app.logger.warning(
                f"Attempt to create a service with an empty price field.")
            flash("Поле \"Стоимость\" обязательно для заполнения", 'danger')
            return render_template('add_service.html', form_data=request.form)

        try:
            new_service = Service(
                service_name=service_name,
                description=description,
                price=price
            )

            db.session.add(new_service)
            db.session.commit()

            app.logger.info(
                f"Service successfully created. ID: {new_service.id}")

            flash("Новая услуга успешно добавлена!", 'success')
            return redirect(url_for('list_services'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Error creating service. ID: {new_service.id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при добавлении новой услуги: {e}")
            flash("Произошла ошибка при добавлении новой услуги", 'danger')
            return render_template('add_service.html', form_data=request.form)

    app.logger.info("The new service creation page has loaded")

    return render_template('add_service.html')


@app.route('/update-service/<int:service_id>', methods=['GET', 'POST'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        price = request.form.get('price')

        app.logger.info(
            f"Start editing service. ID: {service_id}.")

        if is_empty_field(service_name):
            app.logger.warning(
                f"Attempt to send an service with an empty order name field. ID: {service_id}.")
            flash("Поле \"Название услуги\" обязательно для заполнения", 'danger')
            return render_template('update_service.html', service=service)

        if is_empty_field(description):
            app.logger.warning(
                f"Attempt to send an service with an empty order description field. ID: {service_id}.")
            flash("Поле \"Описание услуги\" обязательно для заполнения", 'danger')
            return render_template('update_service.html', service=service)

        if is_empty_field(price):
            app.logger.warning(
                f"Attempt to send an service with an empty order price field. ID: {service_id}.")
            flash("Поле \"Стоимость услуги\" обязательно для заполнения", 'danger')
            return render_template('update_service.html', service=service)

        try:
            service.service_name = service_name
            service.description = description
            service.price = price

            db.session.commit()
            app.logger.info(
                f"Service successfully updated. ID: {service_id}.")
            flash("Данные услуги успешно обновлены!", 'success')
            return redirect(url_for('list_services'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Service modification error. ID: {service_id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при редактировании услуги: {e}")
            flash("Произошла ошибка при обновлении данных услуги", 'danger')

    app.logger.info("Service edit page loaded")

    return render_template('update_service.html', service=service)


@app.route('/delete-service/<int:service_id>', methods=['GET', 'POST'])
def delete_service(service_id):
    try:
        service = Service.query.get_or_404(service_id)

        orders_count = Order.query.filter_by(service_id=service_id).count()

        if orders_count > 0:
            app.logger.warning(
                f"Attempt to delete a service associated with an order(s). ID: {service.id}, Number of orders: {orders_count}.")
            flash(
                f"Невозможно удалить услугу. Есть оформленные заказы с этой услугой: {orders_count}", 'warning')
            return redirect(url_for('list_services'))

        db.session.delete(service)
        db.session.commit()

        app.logger.info(
            f"Service successfully deleted. ID: {service.id}.")

        flash("Услуга успешно удалена!", 'success')
        return redirect(url_for('list_services'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Error deleting service. ID: {service.id}. Error: {str(e)}", exc_info=True)
        print(f"Ошибка при удалении услуги: {e}")
        flash("Произошла ошибка при удалении услуги", 'danger')
        return redirect(url_for('list_services'))


@app.route('/list-services')
def list_services():
    services = Service.query.all()
    app.logger.info("The page with a list of all services has been loaded")
    return render_template('list_services.html', services=services)
# Работа с услугами -->


# <-- Работа с заказами
@app.route('/add-order', methods=['GET', 'POST'])
def add_order():
    customers = Customer.query.all()
    services = Service.query.all()

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')
        order_date = request.form.get('order_date')

        app.logger.info(
            f"Start creating order. Customer: {customer_id}, Service: {service_id}")

        if is_empty_field(customer_id):
            app.logger.warning(
                f"Attempt to create an order with empty fields. Customer: {customer_id}, Service: {service_id}")
            flash("Пожалуйста, выберите клиента", 'danger')
            return render_template('add_order.html', customers=customers, services=services, now=datetime.now)

        if is_empty_field(service_id):
            app.logger.warning(
                f"Attempt to create an order with empty fields. Customer: {customer_id}, Service: {service_id}")
            flash("Пожалуйста, выберите услугу", 'danger')
            return render_template('add_order.html', customers=customers, services=services, now=datetime.now)

        is_valid, message = ValidDate.is_valid_order_date(order_date)
        if not is_valid:
            app.logger.warning(
                f"Attempt to create an order with invalid date of order. Message: {message}")
            flash(message, 'danger')
            return render_template('add_order.html', customers=customers, services=services, now=datetime.now)

        try:
            order_date = datetime.now().date()

            new_order = Order(
                customer_id=customer_id,
                service_id=service_id,
                order_date=order_date
            )

            db.session.add(new_order)
            db.session.commit()

            app.logger.info(
                f"Order successfully created. ID: {new_order.id}, Customer: {customer_id}, Service: {service_id}, Date: {order_date}")

            flash("Заказ успешно оформлен", 'success')
            return redirect(url_for('list_orders'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Error creating order. Customer: {customer_id}, Service: {service_id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при оформлении заказа: {e}")
            flash("Произошла ошибка при оформлении заказа", 'danger')
            return render_template('add_order.html', customers=customers, services=services)

    app.logger.info("The new order creation page has loaded")

    return render_template('add_order.html', customers=customers, services=services, now=datetime.now)


@app.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    customers = Customer.query.all()
    services = Service.query.all()

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')
        order_date = request.form.get('order_date')

        app.logger.info(
            f"Start editing order. Order: {order.id},Customer: {customer_id}, Service: {service_id}")

        if is_empty_field(customer_id):
            app.logger.warning(
                f"Attempt to edit order {order.id} without selecting a customer")
            flash("Пожалуйста, выберите клиента", 'danger')
            return render_template('update_order.html', order=order, customers=customers, services=services, now=datetime.now)

        if is_empty_field(service_id):
            app.logger.warning(
                f"Attempt to edit order {order.id} without selecting a service")
            flash("Пожалуйста, выберите услугу", 'danger')
            return render_template('update_order.html', order=order, customers=customers, services=services, now=datetime.now)

        is_valid, message = ValidDate.is_valid_order_date(order_date)
        if not is_valid:
            app.logger.warning(
                f"Attempt to send an order with an invalid date of order. Message: {message}")
            flash(message, 'danger')
            return render_template('update_order.html', order=order, customers=customers, services=services, now=datetime.now)

        try:
            order.customer_id = customer_id
            order.service_id = service_id

            if order_date and order_date.strip():
                order.order_date = datetime.strptime(
                    order_date, '%Y-%m-%d').date()

            db.session.commit()

            app.logger.info(
                f"Order successfully updated. ID: {order.id}, Customer: {customer_id}, Service: {service_id}, Date: {order_date}")

            flash('Данные заказа успешно обновлены', 'success')
            return redirect(url_for('list_orders'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(
                f"Order modification error. Customer: {customer_id}, Service: {service_id}. Error: {str(e)}", exc_info=True)
            print(f"Ошибка при обновлении заказа: {e}")
            flash('Произошла ошибка при обновлении заказа', 'danger')
            return render_template('update_order.html', order=order, customers=customers, services=services, now=datetime.now)

    app.logger.info("Order edit page loaded")

    return render_template('update_order.html', order=order, customers=customers, services=services, now=datetime.now)


@app.route('/delete-order/<int:order_id>', methods=['GET', 'POST'])
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)

        db.session.delete(order)
        db.session.commit()

        app.logger.info(
            f"Order successfully deleted. ID: {order.id}, Customer: {order.customer_id}, Service: {order.service_id}, Date: {order.order_date}")
        flash("Заказ успешно удален!", 'success')
        return redirect(url_for('list_orders'))

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Error deleting order. ID: {order.id}, Customer: {order.customer_id}, Service: {order.service_id}. Error: {str(e)}", exc_info=True)
        print(f"Ошибка при удалении заказа: {e}")
        flash("Произошла ошибка при удалении заказа", 'danger')
        return redirect(url_for('list_orders'))


@app.route('/list-ordres')
def list_orders():
    orders = Order.query.all()
    app.logger.info("The page with the list of all orders has been loaded")
    return render_template('list_orders.html', orders=orders)
# Работа с заказми -->


if __name__ == "__main__":
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=True
    )
