import os
import pytest

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "True"

from app import app as flask_app
from db import db

@pytest.fixture(scope="session", autouse=True)
def setup_test_config():
    flask_app.config.update({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
    })

@pytest.fixture
def app():
    with flask_app.app_context():
        ### SAFETY CHECK: TO PREVENT TABLE DESTRUCTION
        if "aivencloud" in str(db.engine.url):
            pytest.exit("\n\nCRITICAL ERROR: ENGINE POINTING TO CLOUD DB.\n")
            
        db.create_all()
        yield flask_app
        db.session.remove()
        # Keep this commented out for now!
        # db.drop_all() 

@pytest.fixture
def client(app):
    return app.test_client()