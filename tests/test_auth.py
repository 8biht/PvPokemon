import json


def test_signup_login_refresh_logout(test_env):
    appmod = test_env
    client = appmod.app.test_client()

    # signup
    resp = client.post('/api/v1/signup', json={'username': 'tester', 'password': 's3cret'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('created') is True or data.get('message') == 'Account created'

    # login
    resp = client.post('/api/v1/login', json={'username': 'tester', 'password': 's3cret'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data and 'refresh_token' in data
    access = data['access_token']
    refresh = data['refresh_token']

    # refresh
    resp = client.post('/api/v1/refresh', json={'refresh_token': refresh})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'access_token' in data and 'refresh_token' in data

    # logout (revoke)
    new_refresh = data['refresh_token']
    resp = client.post('/api/v1/logout', json={'refresh_token': new_refresh})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('revoked') is True
