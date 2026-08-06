"""Shared SQL Server database connection for the SQDIP application.

Environment variables:

    DATABASE_SERVER
    DATABASE_NAME

Optional environment variables:

    DATABASE_DRIVER
    DATABASE_USERNAME
    DATABASE_PASSWORD
    DATABASE_TRUSTED_CONNECTION
    DATABASE_ENCRYPT
    DATABASE_TRUST_SERVER_CERTIFICATE
    DATABASE_CONNECTION_TIMEOUT

Example Windows trusted connection:

    DATABASE_SERVER=localhost\\SQLEXPRESS
    DATABASE_NAME=SQDIP
    DATABASE_DRIVER=ODBC Driver 17 for SQL Server
    DATABASE_TRUSTED_CONNECTION=yes
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from dotenv import load_dotenv

import pyodbc


# Load values from a local .env file when python-dotenv is installed.
# The application will still work without python-dotenv when the environment
# variables have been configured through Windows or NSSM.

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if not ENV_FILE.is_file():
    raise RuntimeError(
        f"Environment configuration file was not found: {ENV_FILE}"
    )

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False
)

def get_required_environment_variable(
    variable_name: str
) -> str:
    """Return a required environment variable.

    Raises:
        RuntimeError:
            If the environment variable is missing or empty.
    """

    value = os.getenv(variable_name, "").strip()

    if not value:
        raise RuntimeError(
            f"Required environment variable "
            f"'{variable_name}' is not configured."
        )

    return value


def get_boolean_environment_variable(
    variable_name: str,
    default: bool
) -> bool:
    """Read a yes/no environment variable."""

    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return default

    normalised_value = raw_value.strip().lower()

    if normalised_value in {
        "1",
        "true",
        "yes",
        "y",
        "on"
    }:
        return True

    if normalised_value in {
        "0",
        "false",
        "no",
        "n",
        "off"
    }:
        return False

    raise RuntimeError(
        f"Environment variable '{variable_name}' "
        f"must be yes/no or true/false."
    )


def yes_no(value: bool) -> str:
    """Convert a Boolean value to an ODBC yes/no value."""

    return "yes" if value else "no"


def build_connection_string() -> str:
    """Build the SQL Server ODBC connection string."""

    server = get_required_environment_variable(
        "DATABASE_SERVER"
    )

    database = get_required_environment_variable(
        "DATABASE_NAME"
    )

    driver = os.getenv(
        "DATABASE_DRIVER",
        "ODBC Driver 17 for SQL Server"
    ).strip()

    trusted_connection = (
        get_boolean_environment_variable(
            "DATABASE_TRUSTED_CONNECTION",
            True
        )
    )

    encrypt = get_boolean_environment_variable(
        "DATABASE_ENCRYPT",
        False
    )

    trust_server_certificate = (
        get_boolean_environment_variable(
            "DATABASE_TRUST_SERVER_CERTIFICATE",
            True
        )
    )

    connection_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"Encrypt={yes_no(encrypt)}",
        (
            "TrustServerCertificate="
            f"{yes_no(trust_server_certificate)}"
        ),
    ]

    if trusted_connection:
        connection_parts.append(
            "Trusted_Connection=yes"
        )

    else:
        username = get_required_environment_variable(
            "DATABASE_USERNAME"
        )

        password = get_required_environment_variable(
            "DATABASE_PASSWORD"
        )

        connection_parts.extend([
            f"UID={username}",
            f"PWD={password}",
        ])

    return ";".join(connection_parts) + ";"


def get_db_connection(
    *,
    autocommit: bool = False
) -> pyodbc.Connection:
    """Open and return a SQL Server database connection.

    The caller is responsible for closing the returned connection.

    Example:

        connection = get_db_connection()

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        finally:
            connection.close()
    """

    timeout_text = os.getenv(
        "DATABASE_CONNECTION_TIMEOUT",
        "10"
    ).strip()

    try:
        timeout = int(timeout_text)

    except ValueError as error:
        raise RuntimeError(
            "DATABASE_CONNECTION_TIMEOUT must be "
            "a whole number of seconds."
        ) from error

    if timeout < 1:
        raise RuntimeError(
            "DATABASE_CONNECTION_TIMEOUT must be "
            "at least 1 second."
        )

    connection_string = build_connection_string()

    try:
        connection = pyodbc.connect(
            connection_string,
            timeout=timeout,
            autocommit=autocommit
        )

    except pyodbc.Error as error:
        raise RuntimeError(
            "Unable to connect to the SQL Server "
            "database. Check DATABASE_SERVER, "
            "DATABASE_NAME and the installed ODBC driver."
        ) from error

    return connection


@contextmanager
def database_connection(
    *,
    autocommit: bool = False
) -> Generator[pyodbc.Connection, None, None]:
    """Context manager that closes the connection automatically.

    Successful operations are committed when autocommit is False.
    Failed operations are rolled back.

    Example:

        with database_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE dbo.Example SET Status = ? WHERE ID = ?",
                1,
                100
            )
    """

    connection = get_db_connection(
        autocommit=autocommit
    )

    try:
        yield connection

        if not autocommit:
            connection.commit()

    except Exception:
        if not autocommit:
            connection.rollback()

        raise

    finally:
        connection.close()


def test_database_connection() -> dict[str, str]:
    """Test the connection and return SQL Server information.

    This can be called manually during setup. Do not expose it as a
    public Flask route in the production application.
    """

    sql = """
        SELECT
            CAST(SERVERPROPERTY('ServerName') AS varchar(255))
                AS server_name,

            CAST(DB_NAME() AS varchar(255))
                AS database_name,

            CAST(SERVERPROPERTY('ProductVersion') AS varchar(100))
                AS product_version;
    """

    with database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(sql)

        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "SQL Server returned no connection-test result."
            )

        return {
            "server_name": str(row.server_name),
            "database_name": str(row.database_name),
            "product_version": str(row.product_version),
        }


if __name__ == "__main__":
    try:
        details = test_database_connection()

        print("Database connection successful.")
        print(
            f"Server: {details['server_name']}"
        )
        print(
            f"Database: {details['database_name']}"
        )
        print(
            "SQL Server version: "
            f"{details['product_version']}"
        )

    except Exception as error:
        print("Database connection failed.")
        print(str(error))
        raise