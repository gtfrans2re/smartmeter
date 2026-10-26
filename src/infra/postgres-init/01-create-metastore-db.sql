-- Runs once on first Postgres start (docker-entrypoint-initdb.d).
-- Creates a dedicated database for the Spark/Hive metastore so it is isolated
-- from the Airflow metadata database (both live in the same Postgres instance).
SELECT 'CREATE DATABASE metastore'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metastore')\gexec
