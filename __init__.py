from flask import Flask
from flask_migrate import Migrate
from .extensions import db, login_manager

migrate = Migrate()  # Migration manager

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'secretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.db'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models (needed before using them)
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes.user_routes import user_bp
    from .routes.merchant_routes import merchant_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(merchant_bp)
    app.register_blueprint(admin_bp)

    # ✅ Temporary admin creation route
    @app.route('/create_admin')
    def create_admin():
        from app.models import db, User
        from werkzeug.security import generate_password_hash

        # Prevent duplicate admin
        if User.query.filter_by(username='admin123').first():
            return "Admin already exists."

        # Create admin
        admin = User(
            username='admin123',
            password=generate_password_hash('adminpass'),
            role='admin',
            approved=True
        )
        db.session.add(admin)
        db.session.commit()
        return "✅ Admin user created successfully."

    return app
