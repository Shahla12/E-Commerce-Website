from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, Product, Cart, Order
from datetime import datetime

user_bp = Blueprint('user', __name__)

# ------------------ Home: View all products ------------------
@user_bp.route('/')
def home():
    products = Product.query.all()
    return render_template('user_home.html', products=products)

# ------------------ Register ------------------
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Defaults to 'user'

        # Check if username is already taken
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('user.register'))

        hashed_pw = generate_password_hash(password)

        # ❌ No auto-approval for anyone
        approved = False

        # Create new user
        new_user = User(username=username, password=hashed_pw, role=role, approved=approved)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Await admin approval before logging in.', 'info')
        return redirect(url_for('user.login'))

    return render_template('register.html')


# ------------------ Login ------------------
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # ✅ Block login if not approved (except admin)
            if not user.approved and user.role != 'admin':
                flash("Your account is pending approval by admin.", "warning")
                return redirect(url_for('user.login'))

            login_user(user)
            flash("Login successful!", "success")

            # Redirect by role
            if user.role == 'user':
                return redirect(url_for('user.home'))
            elif user.role == 'merchant':
                return redirect(url_for('merchant.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

        flash("Invalid credentials.", "danger")

    return render_template('login.html')




# ------------------ Logout ------------------
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('user.login'))

# ------------------ Add to Cart ------------------
@user_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    quantity = int(request.form['quantity'])
    product = Product.query.get(product_id)

    if not product or product.stock < quantity:
        flash('Not enough stock or product not found.', 'danger')
        return redirect(url_for('user.home'))

    existing = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.quantity += quantity
    else:
        new_cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)

    db.session.commit()
    flash('Item added to cart.', 'success')
    return redirect(url_for('user.view_cart'))

# ------------------ View Cart ------------------
@user_bp.route('/cart')
@login_required
def view_cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_data = []
    total = 0

    for item in items:
        product = Product.query.get(item.product_id)
        if product:
            subtotal = product.price * item.quantity
            cart_data.append({'product': product, 'quantity': item.quantity, 'subtotal': subtotal})
            total += subtotal

    return render_template('cart.html', cart=cart_data, total=total)

# ------------------ Remove from Cart ------------------
@user_bp.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('user.view_cart'))



# ------------------ View Orders (Order History) ------------------
@user_bp.route('/orders')
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.timestamp.desc()).all()
    return render_template('order_history.html', orders=orders)

# ------------------ Buy Now (Confirm page) ------------------
@user_bp.route('/buy_now/<int:product_id>', methods=['GET', 'POST'])
@login_required
def buy_now(product_id):
    # 🛡 Prevent anyone who is not a user from buying
    if not current_user.is_authenticated or current_user.role != 'user':
        flash("Only approved users can place orders.", "danger")
        return redirect(url_for('user.login'))

    product = Product.query.get(product_id)

    if not product or product.stock < 1:
        flash("Product not available or out of stock.", "danger")
        return redirect(url_for('user.home'))

    if request.method == 'POST':
        quantity = int(request.form['quantity'])

        if quantity < 1 or quantity > product.stock:
            flash("Invalid quantity selected.", "danger")
            return redirect(url_for('user.buy_now', product_id=product.id))

        # Process order
        product.stock -= quantity
        order = Order(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(order)
        db.session.commit()

        flash("✅ Order placed successfully!", "success")
        return redirect(url_for('user.view_orders'))

    return render_template('buy_now.html', product=product)




@user_bp.route('/fix_orders')
@login_required
def fix_orders():
    if current_user.role == 'admin':  # Only admin allowed
        deleted = Order.query.filter_by(user_id=None).delete()
        db.session.commit()
        flash(f"Deleted {deleted} orders with no user.", "info")
    return redirect(url_for('admin.dashboard'))
