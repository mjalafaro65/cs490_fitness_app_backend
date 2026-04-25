import pytest
from app import app as flask_app 
from db import db

@pytest.fixture
def app():
    ### temp app
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "super-secret-test-key"
    })

    with flask_app.app_context():
        db.create_all()
        
        yield flask_app  
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
        ### temp client
    return app.test_client()