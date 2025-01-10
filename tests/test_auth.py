import pytest
from flask_login import current_user
from app.models.user import User

def test_register(client):
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'password2': 'password123'
    })
    assert response.status_code == 302  # Redirect after successful registration
    assert User.query.filter_by(username='newuser').first() is not None

def test_login_logout(client, test_user):
    # Test login
    response = client.post('/login', data={
        'username': 'test',
        'password': 'test123'
    })
    assert response.status_code == 302
    
    # Test that user is logged in
    with client:
        client.get('/')
        assert current_user.is_authenticated
        assert current_user.username == 'test'
    
    # Test logout
    response = client.get('/logout')
    with client:
        client.get('/')
        assert not current_user.is_authenticated 