import pytest
from flask import url_for
import os

def test_set_keys_redirect(client):
    response = client.get(url_for('set_keys'))
    if os.path.exists("secrets.ini"):
        assert response.status_code == 200

def test_set_keys_post(client):
    data = {
        'openai_api_key': '',
        'google_api_key': '',
        'google_cse_id': ''
    }
    response = client.post(url_for('set_keys'), data=data)
    assert response.status_code == 302
    assert response.location.endswith(url_for('upload_page'))
