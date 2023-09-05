import requests

# Create a requests Session
session = requests.Session()

# The "/api/hello" endpoint always works
print(session.get("http://localhost:5000/api/hello").json())

# The following endpoints are login protected and will be rejected
print(session.get("http://localhost:5000/api/test").json())
# print(session.get("http://localhost:5000/api/world").json())
print(session.post("http://localhost:5000/api/foo", json={"fake": "request"}).json())

# Login using the fake username/password
login_response = session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "user", "password": "password"}
)

# Logging in attached cookies to your session
print(session.cookies)

# Now try accessing the protected endpoints again
print(session.get("http://localhost:5000/api/test").json())
print(session.get("http://localhost:5000/api/world").json())
print(session.post("http://localhost:5000/api/foo", json={"fake": "request"}).json())

# Logout
logout_response = session.post("http://localhost:5000/api/auth/logout")

# The session cookies are now gone
print(session.cookies)

# Confirm that you are no longer able to access protected endpoints
print(session.get("http://localhost:5000/api/test").json())
# print(session.get("http://localhost:5000/api/world").json())
print(session.post("http://localhost:5000/api/foo", json={"fake": "request"}).json())