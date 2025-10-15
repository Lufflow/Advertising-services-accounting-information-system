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


@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/add-customer', methods=['POST', 'GET'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        date_of_birth = request.form.get('date_of_birth')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        company = request.form.get('company')

        if not is_valid_phone(phone_number):
            flash(
                'Неверный формат номера телефона. Используйте российский формат', 'danger')
            return redirect(url_for('add_customer'))

        if not is_valid_date(date_of_birth):
            flash('Неверный формат даты. Введите корректную дату', 'danger')
            return redirect(url_for('add_customer'))

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


if __name__ == "__main__":
    app.run(debug=True)
