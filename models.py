from flask_login import UserMixin
from .extensions import db
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user', 'merchant', 'admin'
    approved = db.Column(db.Boolean, default=False)

    # ✅ Relationships
    orders = db.relationship('Order', backref='user', cascade="all, delete", passive_deletes=True)
    carts = db.relationship('Cart', backref='user', cascade="all, delete", passive_deletes=True)
    products = db.relationship('Product', backref='merchant', cascade="all, delete", passive_deletes=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_product_merchant_id'),
        nullable=False
    )

    orders = db.relationship('Order', backref='product', cascade="all, delete", passive_deletes=True)
    carts = db.relationship('Cart', backref='product', cascade="all, delete", passive_deletes=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_cart_user_id'),
        nullable=False
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id', ondelete='CASCADE', name='fk_cart_product_id'),
        nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_order_user_id'),
        nullable=False
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id', ondelete='CASCADE', name='fk_order_product_id'),
        nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
