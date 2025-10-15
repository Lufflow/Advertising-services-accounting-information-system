from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(125), nullable=False)
    date_of_birth = db.Column(db.Date)
    phone_number = db.Column(
        db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(100))
    company = db.Column(db.String(100))

    def __repr__(self):
        return f'<Customer {self.name} {self.phone_number}>'


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(125), nullable=False)
    description = db.Column(db.Text(1000))
    price = db.Column(db.Float(), nullable=False, default='0')


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey(
        'customers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey(
        'services.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)

    customer = db.relationship('Customer', backref='orders')
    service = db.relationship('Service', backref='orders')
