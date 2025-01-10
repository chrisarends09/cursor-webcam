import pytest
from app import create_app, db
from app.models.user import User
from app.models.webcam import Webcam

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    user = User(username='test', email='test@example.com')
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_webcam(app):
    webcam = Webcam(
        name='Test Webcam',
        description='Test Description',
        url='http://example.com/webcam',
        type='direct_image',
        resort='test_resort'
    )
    db.session.add(webcam)
    db.session.commit()
    return webcam 