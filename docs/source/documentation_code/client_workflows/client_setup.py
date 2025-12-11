from dioptra.client import connect_json_dioptra_client

DIOPTRA_REST_API_ADDRESS = "http://localhost:5000"
DIOPTRA_REST_API_USER = "<user>"
DIOPTRA_REST_API_PASS = "<password>"

client = connect_json_dioptra_client(DIOPTRA_REST_API_ADDRESS)

# if you have not yet registered a user, uncomment the following line and adjust the parameters as desired to register a user first
# client.users.create(DIOPTRA_REST_API_USER, email=f"{DIOPTRA_REST_API_USER}@localhost", password=DIOPTRA_REST_API_PASS)

client.auth.login(DIOPTRA_REST_API_USER, DIOPTRA_REST_API_PASS)