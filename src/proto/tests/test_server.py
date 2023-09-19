import pytest

from proto.app import create_app

import logging


@pytest.fixture
def client():
    with create_app().test_client() as client:
        yield client

def test_user_login(client):
    response = client.post('/api/auth/login', json={"username": "user", "password": "password"})
    assert response.status_code == 200
    #assert b'Logged in successfully' in response.data

def test_world_api(client):
    logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

    #first login
    response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
    assert response.status_code == 200

    #set cookie


    #then access test_api resource
    response = client.get('/api/world', follow_redirects=True)
    assert response.status_code == 200
    logging.debug("Response: ",response)


# def test_world_api(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access test_api resource
#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

# def test_pulic_hello_api(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "not_allowed", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #then access hello_api resource, which will always pass as it is set to public
#     response = client.get('/api/hello', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

# def test_world_api_decorator_other_user(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "tester", "password": "testing"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access test_api resource
#     response = client.put('/api/world', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

# def test_world_api_admin_decorator(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access test_api resource
#     response = client.post('/api/world', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)


# def test_share_read(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access share the world resource with devs who don't have access
#     response = client.post('/api/user/shareread',
#                         json ={"resource_name" : "world", "group_name": "devs"},
#                         follow_redirects=True)
#     assert response.status_code == 200

#     #logout
#     response = client.post("/api/auth/logout")
#     assert response.status_code == 200

#     response = client.post('/api/auth/login', json={"username": "joe", "password": "hashed"}, follow_redirects=True)
#     assert response.status_code == 200

#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200


#     logging.debug("Response: ",response)

# def test_revoke_share_read(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access share the world resource with devs who don't have access
#     response = client.post('/api/user/shareread',
#                         json ={"resource_name" : "world", "group_name": "devs"},
#                         follow_redirects=True)
#     assert response.status_code == 200

#     #logout
#     response = client.post("/api/auth/logout")
#     assert response.status_code == 200

#     #now devs can read
#     response = client.post('/api/auth/login', json={"username": "joe", "password": "hashed"}, follow_redirects=True)
#     assert response.status_code == 200

#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200

#     #logout
#     response = client.post("/api/auth/logout")
#     assert response.status_code == 200

#     #login as admin
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #then access revoke the world resource reading from devs
#     response = client.post('/api/user/revokeshareread',
#                         json ={"resource_name" : "world", "group_name": "devs"},
#                         follow_redirects=True)
#     assert response.status_code == 200


#     #logout
#     response = client.post("/api/auth/logout")
#     assert response.status_code == 200

#     response = client.post('/api/auth/login', json={"username": "joe", "password": "hashed"}, follow_redirects=True)
#     assert response.status_code == 200

#     #now devs cannot read
#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 404 


#     logging.debug("Response: ",response)


# @pytest.mark.xfail
# def test_share_fail(client):
#     response = client.post('/api/auth/login', json={"username": "joe", "password": "hashed"}, follow_redirects=True)
#     assert response.status_code == 200

#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200


#     logging.debug("Response: ",response)

# @pytest.mark.xfail
# def test_world_api_disallow(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "not_allowed", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #then access world_api resource
#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

# @pytest.mark.xfail
# def test_world_api_disallow_devs(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "joe", "password": "hashed"}, follow_redirects=True)
#     assert response.status_code == 200

#     #then access world_api resource
#     response = client.get('/api/world', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

# @pytest.mark.xfail
# def test_test_api_admin_fail(client):
#     logging.basicConfig(level=logging.DEBUG)  # Set the log level
    

#     #first login
#     response = client.post('/api/auth/login', json={"username": "user", "password": "password"}, follow_redirects=True)
#     assert response.status_code == 200

#     #set cookie


#     #then access test_api resource
#     response = client.get('/api/test', follow_redirects=True)
#     assert response.status_code == 200
#     logging.debug("Response: ",response)

