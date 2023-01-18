echo "CREATE DATABASE parsers; \n
    CREATE USER root WITH PASSWORD 'root'; \n
    ALTER ROLE root SET client_encoding TO 'utf8'; \n
    ALTER ROLE root SET default_transaction_isolation TO 'read committed'; \n
    ALTER ROLE root SET timezone TO 'UTC'; \n
    GRANT ALL PRIVILEGES ON DATABASE parsers TO root;" | sudo -i -u postgres psql
