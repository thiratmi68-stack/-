import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, g
from flask_cors import CORS
from backend.database import close_db, startup, DB_PATH

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register Teardown
    app.teardown_appcontext(close_db)
    
    # Import Blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.bookings import bookings_bp
    from backend.routes.doctors import doctors_bp
    from backend.routes.admin import admin_bp
    from backend.routes.notifications import notifications_bp
    from backend.routes.pages import pages_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(doctors_bp, url_prefix='/api') # doctors.py has /doctors and /departments
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(pages_bp, url_prefix='/')

    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    
    with app.app_context():
        startup() # This calls init_db
        
    app.run(host='0.0.0.0', port=5000, debug=True)
