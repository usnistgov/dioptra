# Flask Prototype

A simple Flask prototype for learning purposes.

<!-- markdownlint-disable MD007 MD030 -->
- [Quickstart](#quickstart)
- [Setup](#setup)
    - [Installation](#installation)
    - [Generating the requirements lockfiles](#generating-the-requirements-lockfiles)
- [Examples](#examples)
    - [Same user, multiple devices](#same-user-multiple-devices)
    - [Multiple users](#multiple-users)
    - [User management](#user-management)
<!-- markdownlint-enable MD007 MD030 -->

## Quickstart

Open a terminal in the `flask-prototype` folder, [install the prototype application in a Python 3.9 virtual environment](#setup), and start a Flask development server,

    # Runs the server on http://localhost:5000
    flask run

    # If the above doesn't seem to work, try this
    flask run --host ::1

To see the Swagger Docs for the REST API, open <http://localhost:5000/api> in your web browser.

To test out sending requests to the API, open a second terminal in the `flask-prototype` folder, activate the same virtual environment, and start an interactive Python session,

    # Interactive session on the command-line
    ipython

    # Starts JupyterLab - If you use this open a new notebook
    jupyter lab

The code below shows how you can interact with the simple Flask prototype using the Python `requests` package,

```python
import requests


# Create a requests Session
session = requests.Session()

# The "/api/hello" endpoint always works
print(session.get("http://localhost:5000/api/hello").json())

# The following endpoints are login protected and will be rejected
print(session.get("http://localhost:5000/api/test").json())
print(session.get("http://localhost:5000/api/world").json())
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
print(session.get("http://localhost:5000/api/world").json())
print(session.post("http://localhost:5000/api/foo", json={"fake": "request"}).json())
```

To stop the Flask development server, switch back to the first terminal window and press <kbd>Ctrl</kbd>+<kbd>C</kbd>.

Additional examples can be found in the [Examples section of this README](#examples).

## Setup

This project requires you to install the following software on your computer,

-   [Python 3.9](https://www.python.org)

### Installation

Create a Python 3.9 virtual environment,

    # "python" is assumed to be an alias for your Python 3.9 interpreter
    python -m venv .venv

Activate the virtual environment,

    # MacOS/Linux
    source .venv/bin/activate

    # Windows - Command Prompt/Powershell
    .venv\Scripts\activate

Upgrade `pip` and install the `pip-tools` package,

    python -m pip install --upgrade pip pip-tools

Use `pip-sync` to install the prototype's dependencies for your operating system and platform:

    # MacOS - x86_64
    pip-sync requirements requirements/macos-x86_64-py3.9-requirements-dev.txt

    # MacOS - arm64 (Apple Silicon)
    pip-sync requirements requirements/macos-arm64-py3.9-requirements-dev.txt

    # Linux - x86_64
    pip-sync requirements requirements/linux-x86_64-py3.9-requirements-dev.txt

    # Linux - arm64 (aarch64)
    pip-sync requirements requirements/linux-aarch64-py3.9-requirements-dev.txt

If there is no lockfile for your operating system and platform, [see the next section for instructions on how to generate one](#generating-the-requirements-lockfiles).

### Generating the requirements lockfiles

To (re)generate the requirements lockfiles, start by creating a Python 3.9 virtual environment if you haven't already,

    # "python" is assumed to be an alias for your Python 3.9 interpreter
    python -m venv .venv

Activate the virtual environment,

    # MacOS/Linux
    source .venv/bin/activate

    # Windows - Command Prompt/Powershell
    .venv\Scripts\activate

Upgrade `pip` and install the `pip-tools` and `tox` packages,

    python -m pip install --upgrade pip pip-tools tox

Generate the lockfile for your operating system and platform:

    # MacOS - x86_64
    python -m tox run -e py39-macos-x86_64-requirements-dev

    # MacOS - arm64 (Apple Silicon)
    python -m tox run -e py39-macos-aarch64-requirements-dev

    # Linux - x86_64
    python -m tox run -e py39-linux-x86_64-requirements-dev

    # Linux - arm64 (aarch64)
    python -m tox run -e py39-linux-aarch64-requirements-dev

    # Windows - x86_64
    python -m tox run -e py39-win-x86_64-requirements-dev

Afterwards, use `pip-sync` [as described in the previous section](#installation) to upgrade your virtual environment using the newly generated lockfile.

## Examples

### Same user, multiple devices

Logging into the application stores a cookie in your session:

```python
import requests


# Create a session and login
session1 = requests.Session()
login_response1 = session1.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "user", "password": "password"}
)

# The user's session is stored as a client-side cookie.
print(session1.cookies)
```

We can simulate logging in from multiple devices by creating multiple sessions:

```python
# Create a second session and login
session2 = requests.Session()
login_response2 = session2.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "user", "password": "password"},
)
```

Logging out from one session does not affect the other:

```python
# Logout
logout_response1 = session1.post("http://localhost:5000/api/auth/logout")

# The session cookie is cleared from the first session
print(session1.cookies)

# The session cookie remains on the second session
print(session2.cookies)

# We cannot access protected endpoints from the first session
print(session1.get("http://localhost:5000/api/world").json())

# But we can still access them from the second session
print(session2.get("http://localhost:5000/api/world").json())
```

In contrast, issuing a "full" logout using the query parameter `everywhere=true` logs every device out:

```python
# Create a third session, login, then do a full logout
session3 = requests.Session()
login_response3 = session3.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "user", "password": "password"},
)
logout_response3 = session3.post(
    "http://localhost:5000/api/auth/logout",
    params={"everywhere": True},
)

# As expected, we cannot access protected endpoints from the third session
print(session3.get("http://localhost:5000/api/world").json())

# We cannot access protected endpoints from the second session due to the full logout
print(session2.get("http://localhost:5000/api/world").json())
```

### Multiple users

We can demonstrate that sessions automatically keep track of the user that is logged in across multiple users:

```python
import requests


# Create a session and login with user:password
user_session = requests.Session()
user_login_response = user_session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "user", "password": "password"}
)

# Create a session and login with joe:hashed
joe_session = requests.Session()
joe_login_response = joe_session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "joe", "password": "hashed"}
)
```

We send a request to the `/api/world` endpoint to retrieve information about the current user for each session:

```python
print(user_session.get("http://localhost:5000/api/world").json())
# {'id': 1, 'alternative_id': '...', 'name': 'user', 'password': '...', 'deleted': False}

print(joe_session.get("http://localhost:5000/api/world").json())
# {'id': 2, 'alternative_id': '...', 'name': 'joe', 'password': '...', 'deleted': False}
```

Doing a full logout on the "user" session will not affect the "joe" session:

```python
user_logout_response = user_session.post(
    "http://localhost:5000/api/auth/logout", params={"everywhere": True}
)

print(joe_session.get("http://localhost:5000/api/foo").json())
# 'bar'
```

### User management

The application has basic support for creating new user accounts:

```python
import requests


# Create a session and register a new account with credentials new_user:new_password
session = requests.Session()
registration_response = session.post(
    "http://localhost:5000/api/user",
    json={
        "name": "new_user",
        "password": "new_password",
        "confirmPassword": "new_password",
    },
)

# Login with new_user account and confirm access to protected endpoints
login_response = session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "new_user", "password": "new_password"},
)

print(session.get("http://localhost:5000/api/world").json())
# {'id': 3, 'alternative_id': '...', 'name': 'new_user', 'password': '...', 'deleted': False}
```

You can change a password on an existing account:

```python
session.post(
    "http://localhost:5000/api/user/password",
    json={
        "currentPassword": "new_password",
        "newPassword": "updated_password",
    },
)

# Confirm that changing the password logs the user out on all devices
print(session.get("http://localhost:5000/api/world").json())

# Login with the updated password and confirm access to the protected endpoint
login_response = session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "new_user", "password": "updated_password"},
)
print(session.get("http://localhost:5000/api/world").json())
```

You can also delete an account:

```python
delete_response = session.delete(
    "http://localhost:5000/api/user",
    json={"password": "updated_password"},
)

# Confirm that you no longer have access to a protected endpoint
print(session.get("http://localhost:5000/api/world").json())

# Confirm that you can no longer login to the account
login_response = session.post(
    "http://localhost:5000/api/auth/login",
    json={"username": "new_user", "password": "updated_password"}
)
print(login_response.json())
```
