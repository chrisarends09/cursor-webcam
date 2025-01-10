import pytest
from app.models.webcam import Webcam, UserWebcam

def test_add_webcam(client, test_user):
    # Login first
    client.post('/login', data={
        'username': 'test',
        'password': 'test123'
    })
    
    # Add webcam
    response = client.post('/webcam/add', data={
        'name': 'New Webcam',
        'description': 'Test Description',
        'url': 'http://example.com/webcam',
        'type': 'direct_image',
        'resort': 'test_resort'
    })
    assert response.status_code == 302
    assert Webcam.query.filter_by(name='New Webcam').first() is not None

def test_select_webcam(client, test_user, test_webcam):
    # Login first
    client.post('/login', data={
        'username': 'test',
        'password': 'test123'
    })
    
    # Select webcam with interval
    response = client.post(f'/webcam/select/{test_webcam.id}', data={
        'interval': '1'
    })
    assert response.status_code == 302
    user_webcam = UserWebcam.query.filter_by(
        user_id=test_user.id,
        webcam_id=test_webcam.id
    ).first()
    assert user_webcam is not None
    assert user_webcam.interval_hours == 1 