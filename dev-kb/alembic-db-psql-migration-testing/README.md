# This guide describes Postgres container setup

#### The environment setup can be used for testing the Alembic migration scripts compatibility with the Postgres (pSQL) database in the container


## Docker compose (mostly self-contained) Postgres-setup
##### (more error prone, but allows easier adjustments, when needed)


## Completely manual docker Postgres-setup
##### (more error prone, but allows easier adjustments, when needed)

### !!! Important Note !!!:
#### If you intend to use `$`, `!` in your database password (the superset of the `special` characters will depend on your OS and shell of preference) - remember to escape or URL-encode these characters in the appropriate contexts. Otherwise, the password/authentication errors may arise in the shell connection string and/or in the environment variable(s) use/set time.

#### It is simple to URL-encode password in Python
```python
import urllib.parse
# Replace the example 'my\@pas$s$/word! 123~!@#' with your password with special characters
password = "my\@pas$s$/word! 123~!@#" # Simply an illustration of a password
# URL-encode the password
encoded_password = urllib.parse.quote_plus(password)
print(encoded_password)

```
#### The above code results in the following output:
```
>>> my%5C%40pas%24s%24%2Fword%21+123~%21%40%23
```

1.  Pull docker container from docker repository
```sh
docker pull postgres:15
```

2.  Create a DB-hosting volume
```sh
docker volume create postgres-volume
```

3.  Start the pSQL container with the database instance
``` sh
docker run \
--name test_postgres \
-e POSTGRES_PASSWORD=<your-pSQL-DB-password> \
-p 5432:5432 \
--mount type=volume,src=postgres-volume,dst=/var/lib/postgresql/data \
-d postgres:15
```

```sh
docker run --name di_tp -e POSTGRES_PASSWORD=<your-pSQL-DB-password> -p 5432:5432 --mount type=volume,src=postgres-volume,dst=/var/lib/postgresql/data -d postgres:15
```




4. Access shell environment in the container:
```sh
docker exec -it  test_postgres /bin/bash
```

5. Access pSQL CLI to manage Postgres user(s) and database(s) assuming the default user name `postgres`
```sh
psql -U postgres
```
6. In the psql CLI environment run the following commands:

- Add user named `dioptra` with a `<your-dioptra-DB-password>` to the Postgress DB:
```SQL
CREATE USER dioptra WITH PASSWORD '<your-dioptra-DB-password>';
```

- Create the `restapi` database and give ownership to `dioptra` user:
```SQL
CREATE DATABASE restapi OWNER dioptra;
```

- Make sure that the ownership of the database `restapi` is correctly given to the `dioptra` user with the pSQL shortcut command
```sql
\l
```

- (Optional) Exit psql CLI with `\q` command
- (Optional) Exit the container with `exit` command


6. After you are done - reset the container to run the scripts again by deleting the DB-containing volume

```sh
docker stop test_postgres
docker rm test_postgres

docker volume rm postgres-volume
```
