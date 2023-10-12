import pytest

from proto.app import create_app

import logging

from typing import Iterable

from flask import Flask
from flask.testing import FlaskClient


# @pytest.fixture
# def client():
#     with create_app().test_client() as client:
#         yield client


class TestUser(object):
    @pytest.fixture(scope="class")
    def app(self) -> Iterable[Flask]:
        app: Flask = create_app(include_test_data=True)
        yield app

    @pytest.fixture(scope="class")
    def client(self, app: Flask) -> FlaskClient:
        return app.test_client()
    
    @pytest.fixture(scope="class")
    def login(self, client: FlaskClient) -> Iterable[None]:
        with client:
            _ = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            )
            yield

    def test_world_api(self, client, login):        
        #then access test_api resource
        response = client.get('/api/world', follow_redirects=True)
        assert response.status_code == 200

    def test_world_api2(self, client, login):        
        #the presence of this second seemingly redundant test is to confirm the behavior of
        #run once decorator breaking pytest
        response = client.get('/api/world', follow_redirects=True)
        assert response.status_code == 200

    def test_allow_user_on_test_read(self, client,login):
        #then access test resource
        response = client.get('/api/test', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.xfail
    def test_disallow_user_on_test_post(self, client, login):
        #then access test_api resource
        response = client.post('/api/test', follow_redirects=True)
        assert response.status_code == 200


class TestJoe(object):
    @pytest.fixture(scope="class")
    def app(self) -> Iterable[Flask]:
        app: Flask = create_app(include_test_data=True)
        yield app

    @pytest.fixture(scope="class")
    def client(self, app: Flask) -> FlaskClient:
        return app.test_client()
    
    @pytest.fixture(scope="class")
    def login(self, client: FlaskClient) -> Iterable[None]:
        with client:
            _ = client.post(
                "/api/auth/login",
                json={"username": "joe", "password": "hashed"},
            )
            yield
    
    def test_allow_joe_on_test_get(self, client, login):

        response = client.get('/api/test', follow_redirects=True)
        assert response.status_code == 200
        logging.debug("Response: ", response)

    @pytest.mark.xfail
    def test_disallow_joe_on_world_get(self, client, login):

        response = client.get('/api/world', follow_redirects=True)
        assert response.status_code == 200
        logging.debug("Response: ", response)

class TestGroup(object):
    @pytest.fixture(scope="class")
    def app(self) -> Iterable[Flask]:
        app: Flask = create_app(include_test_data=True)
        yield app

    @pytest.fixture(scope="class")
    def client(self, app: Flask) -> FlaskClient:
        return app.test_client()
    
    @pytest.fixture(scope="class")
    def login(self, client: FlaskClient) -> Iterable[None]:
        with client:
            _ = client.post(
                "/api/auth/login",
                json={"username": "user", "password": "password"},
            )
            yield

    def test_create_group_api(self, client, login):
        #create group

        #data
        json={"name": "created_group"}
        #post
        response = client.post('/api/group', json = json, follow_redirects=True)
        assert response.status_code == 200

    def test_share_to_group(self, client, login):
        #data
        json={"resource_id":1, "group_id": 3, "readable": True, "writable": False}
        #post
        response = client.post('/api/sharing/share', json = json, follow_redirects=True)
        assert response.status_code == 200

    def test_add_user_to_group_for_read(self, client,login):
        #add user to new group with read perms

        #data
        json={"user_id":2, "group_id": 3, "read": True, "write": True, "share_read": True, "share_write": True}
        #post
        response = client.put('/api/group', json = json, follow_redirects=True)
        assert response.status_code == 200
    
    def test_access_shared_resource_read(self, client,login):
        #logout
        response = client.post("/api/auth/logout")
        assert response.status_code == 200

        #login as user 2
        _ = client.post(
                "/api/auth/login",
                json={"username": "joe", "password": "hashed"},
            )
        
        #then access test shared resource
        #data
        json={"resource_id":2, "action_name": "read"}
        #post
        response = client.get('/api/sharing', json = json, follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.xfail
    def test_disallow_user_on_shared_resource(self, client, login):
        #then access test_api resource
        response = client.post('/api/test', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.xfail
    def test_disallow_user_on_shared_resource_write(self, client, login):
        #then access test_api resource
        response = client.post('/api/test', follow_redirects=True)
        assert response.status_code == 200

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

