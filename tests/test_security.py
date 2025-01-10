import pytest
from flask import url_for
import jwt
from datetime import datetime, timedelta

def test_security_headers(client):
    """Test that security headers are present in responses"""
    response = client.get('/')
    
    assert response.headers.get('Content-Security-Policy') is not None
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'
    assert response.headers.get('Strict-Transport-Security') is not None

def test_rate_limiting(client, test_user):
    """Test rate limiting functionality"""
    # Login first
    client.post('/login', data={
        'username': 'test',
        'password': 'test123'
    })
    
    # Make multiple requests
    for _ in range(101):  # Limit is 100
        response = client.get('/api/webcams')
    
    assert response.status_code == 429
    assert 'retry_after' in response.json

def test_api_token_auth(client, test_user, app):
    """Test API token authentication"""
    # Get token
    response = client.post('/api/auth/token')
    assert response.status_code == 401  # Not logged in
    
    # Login and get token
    client.post('/login', data={
        'username': 'test',
        'password': 'test123'
    })
    response = client.post('/api/auth/token')
    assert response.status_code == 200
    assert 'token' in response.json
    
    # Use token
    token = response.json['token']
    response = client.get('/api/system/status', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200

def test_cors_headers(client):
    """Test CORS headers"""
    response = client.options('/api/webcams', headers={
        'Origin': 'http://localhost:5000',
        'Access-Control-Request-Method': 'GET'
    })
    
    assert response.headers.get('Access-Control-Allow-Methods')
    assert response.headers.get('Access-Control-Allow-Headers')
    assert response.headers.get('Access-Control-Max-Age') 