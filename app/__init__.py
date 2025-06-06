# app/__init__.py

from flask import Flask, session, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel

# Inicialización de extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # CORRECTO: redirige a /login en blueprint 'auth'
babel = Babel()

def create_app():
    app = Flask(__name__)

    # Configuración básica
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'es'

    # Inicialización de extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    babel.init_app(app)

    # Importación de modelos
    from .models import Empleado

    # Carga de usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Empleado.query.get(int(user_id))

    # Registro de blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Crear tablas
    with app.app_context():
        db.create_all()

    # Filtro Jinja para nombre del mes
    import calendar
    app.jinja_env.filters['month_name'] = lambda m: calendar.month_name[m]

    return app


# Locale para Flask-Babel
def get_locale():
    return session.get('lang') or request.accept_languages.best_match(['es', 'en'])
