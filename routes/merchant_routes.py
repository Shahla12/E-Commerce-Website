from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, Product, Order

merchant_bp = Blueprint('merchant', __name__, url_prefix='/merchant')

# ------------------ Register ------------------
@merchant_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('merchant.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            role='merchant',
            approved=False
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully! Await admin approval.", "success")
        return redirect(url_for('merchant.login'))

    return render_template('merchant/register.html')

# ------------------ Login ------------------
@merchant_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='merchant').first()

        if user and check_password_hash(user.password, password):
            if user.approved:
                login_user(user)
                flash("Login successful", "success")
                return redirect(url_for('merchant.dashboard'))
            else:
                flash("Your account is pending admin approval.", "warning")
        else:
            flash("Invalid credentials", "danger")

    return render_template('merchant/login.html')

# ------------------ Dashboard ------------------
@merchant_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'merchant':
        flash("Unauthorized access", "danger")
        return redirect(url_for('merchant.login'))

    products = Product.query.filter_by(merchant_id=current_user.id).all()
    return render_template('merchant/merchant_dashboard.html', products=products)

# ------------------ Show Add Product Form ------------------
@merchant_bp.route('/add_product', methods=['GET'])
@login_required
def add_product_form():
    if current_user.role != 'merchant':
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.login'))
    return render_template('merchant_addProducts.html')

# ------------------ Add Product (POST handler) ------------------
@merchant_bp.route('/add', methods=['POST'])
@login_required
def add_product():
    if current_user.role != 'merchant':
        return redirect(url_for('merchant.login'))

    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form['stock'])

    new_product = Product(
        name=name,
        price=price,
        stock=stock,
        merchant_id=current_user.id
    )
    db.session.add(new_product)
    db.session.commit()
    flash("Product added", "success")
    return redirect(url_for('merchant.dashboard'))

# ------------------ Restock Product ------------------
@merchant_bp.route('/restock/<int:product_id>', methods=['POST'])
@login_required
def restock(product_id):
    quantity_str = request.form.get('quantity', '').strip()

    if not quantity_str.isdigit() or int(quantity_str) <= 0:
        flash("Please enter a valid quantity.", "warning")
        return redirect(url_for('merchant.dashboard'))

    quantity = int(quantity_str)
    product = Product.query.get_or_404(product_id)

    if product.merchant_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    product.stock += quantity
    db.session.commit()
    flash("Product restocked", "info")
    return redirect(url_for('merchant.dashboard'))


# ------------------ Delete Product ------------------
@merchant_bp.route('/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.merchant_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    db.session.delete(product)
    db.session.commit()
    flash("Product deleted", "danger")
    return redirect(url_for('merchant.dashboard'))

# ------------------ View Orders ------------------
@merchant_bp.route('/orders')
@login_required
def view_orders():
    if current_user.role != 'merchant':
        return redirect(url_for('merchant.login'))

    orders = Order.query.join(Product).filter(Product.merchant_id == current_user.id).all()

    order_data = [{
        'product_name': order.product.name,
        'quantity': order.quantity,
        'buyer': User.query.get(order.user_id).username,
        'timestamp': order.timestamp
    } for order in orders]

    return render_template('merchant/merchant_orders.html', orders=order_data)

# ------------------ Logout ------------------
@merchant_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for('user.login'))          #shared login page for user and merchant


# ------------------ Show Edit Product Form ------------------
@merchant_bp.route('/edit/<int:product_id>', methods=['GET'])
@login_required
def edit_product_form(product_id):
    product = Product.query.get_or_404(product_id)

    if product.merchant_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    return render_template('merchant/merchant_editProduct.html', product=product)

# ------------------ Handle Product Edit ------------------
@merchant_bp.route('/update/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.merchant_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    product.name = request.form['name']
    product.price = float(request.form['price'])
    product.stock = int(request.form['stock'])

    db.session.commit()
    flash("Product updated successfully", "success")
    return redirect(url_for('merchant.dashboard'))


@merchant_bp.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    if current_user.role != 'merchant':  # or 'moderator'
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    user = User.query.get(user_id)
    if user and user.role in ['user', 'merchant']:
        user.approved = True
        db.session.commit()
        flash(f"{user.username} has been approved.", "success")
    return redirect(url_for('merchant.manage_users'))  # your custom page



@merchant_bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'merchant':  # or 'moderator'
        flash("Unauthorized", "danger")
        return redirect(url_for('merchant.dashboard'))

    user = User.query.get(user_id)
    if user and user.role in ['user', 'merchant']:
        db.session.delete(user)
        db.session.commit()
        flash(f"{user.username} has been deleted.", "warning")
    return redirect(url_for('merchant.manage_users'))

