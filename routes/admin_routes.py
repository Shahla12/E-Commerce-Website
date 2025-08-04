from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, Product, Order,Cart
from app.extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin Login
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='admin').first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid admin credentials.", "danger")

    return render_template('admin/login.html')

# Admin Dashboard (menu only)
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))
    return render_template('admin/dashboard.html')

# View Users & Merchants
@admin_bp.route('/users')
@login_required
def view_users():
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))

    users = User.query.filter_by(role='user').all()
    merchants = User.query.filter_by(role='merchant').all()
    return render_template('admin/users.html', users=users, merchants=merchants)

# View All Products
@admin_bp.route('/products')
@login_required
def view_products():
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))

    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# View All Orders
@admin_bp.route('/orders')
@login_required
def view_orders():
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))

    orders = Order.query.all()
    return render_template('admin/orders.html', orders=orders)

# Approve User or Merchant
@admin_bp.route('/approve/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))

    user = User.query.get(user_id)
    if user:
        user.approved = True
        db.session.commit()
        flash(f"{user.username} approved successfully.", "success")
    return redirect(url_for('admin.view_users'))


# Delete User or Merchant
@admin_bp.route('/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied", "danger")
        return redirect(url_for('admin.login'))

    user = User.query.get(user_id)
    if user:
        # First, delete all related orders
        Order.query.filter_by(user_id=user.id).delete()

        # Optionally, delete related cart items too
        Cart.query.filter_by(user_id=user.id).delete()

        db.session.delete(user)
        db.session.commit()
        flash(f"{user.username} and related data deleted.", "warning")
    return redirect(url_for('admin.view_users'))




# Admin Logout
@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")

    return redirect(url_for('admin.login'))
