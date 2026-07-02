from flask import Flask
from models import db
from routes import register_routes
import os

def create_app():
    app = Flask(__name__)
    
    # Configure SQLite database
    basedir = os.path.abspath(os.path.dirname(__name__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'super-secret-key-change-in-production' # Required for session management
    
    db.init_app(app)
    
    with app.app_context():
        # db.drop_all() # Uncomment to reset database during development
        db.create_all()
        _create_default_admin()
        
    register_routes(app)
    
    return app

def _create_default_admin():
    from models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        new_admin = User(username='admin', role='admin')
        new_admin.set_password('admin123')
        db.session.add(new_admin)
        db.session.commit()
        print("Default admin created: admin / admin123")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
