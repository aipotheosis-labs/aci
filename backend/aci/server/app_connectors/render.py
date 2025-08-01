from typing import Any, cast, override

import requests
from sqlalchemy import create_engine, text

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


class Render(AppConnectorBase):
    """
    Render Connector for executing SQL queries on Render PostgreSQL databases.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: APIKeyScheme,
        security_credentials: APIKeySchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.api_key = security_credentials.secret_key
        self.base_url = "https://api.render.com"

    @override
    def _before_execute(self) -> None:
        pass

    def run_sql_query(
        self,
        workspace_id: str,
        database_id: str,
        sql: str,
    ) -> dict[str, Any]:
        """
        Execute a SQL query on a Render PostgreSQL database.

        Args:
            workspace_id: The ID of the workspace/owner that contains the database
            database_id: The ID of the PostgreSQL database instance to query
            sql: The SQL query to execute

        Returns:
            dict: Query results and metadata
        """
        logger.info(f"Executing SQL query on Render database: {database_id}")

        try:
            # Get connection information from Render API
            connection_info = self._get_postgres_connection_info(database_id)

            # Create connection URL
            connection_url = self._build_connection_url(connection_info)

            # Execute the SQL query synchronously
            result = self._execute_query_sync(connection_url, sql)

            return {
                "success": True,
                "database_id": database_id,
                "workspace_id": workspace_id,
                "rows_affected": result.get("rows_affected", 0),
                "data": result.get("data", []),
                "column_names": result.get("column_names", []),
            }

        except Exception as e:
            logger.error(f"Error executing SQL query: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "database_id": database_id,
                "workspace_id": workspace_id,
            }

    def _get_postgres_connection_info(self, postgres_id: str) -> dict[str, Any]:
        """
        Get PostgreSQL connection information from Render API.

        Args:
            postgres_id: The ID of the PostgreSQL instance

        Returns:
            dict: Connection information including host, port, database name, user, password
        """
        url = f"{self.base_url}/v1/postgres/{postgres_id}/connection-info"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()  # type: ignore[no-any-return]

    def _build_connection_url(self, connection_info: dict[str, Any]) -> str:
        """
        Build PostgreSQL connection URL from connection information.

        Args:
            connection_info: Connection information from Render API

        Returns:
            str: PostgreSQL connection URL for async SQLAlchemy
        """
        # Get the external connection string from Render API response
        conn_str = connection_info.get("externalConnectionString")

        if not conn_str or not isinstance(conn_str, str):
            raise ValueError("Unable to find externalConnectionString in Render API response")

        # Convert standard PostgreSQL URL to sync psycopg URL
        if conn_str.startswith("postgresql://"):
            return cast(str, conn_str.replace("postgresql://", "postgresql+psycopg2://", 1))
        elif conn_str.startswith("postgres://"):
            return cast(str, conn_str.replace("postgres://", "postgresql+psycopg2://", 1))
        else:
            raise ValueError(f"Unexpected connection string format: {conn_str}")

    def _execute_query_sync(self, connection_url: str, sql: str) -> dict[str, Any]:
        """
        Execute SQL query synchronously using SQLAlchemy.

        Args:
            connection_url: PostgreSQL connection URL
            sql: SQL query to execute

        Returns:
            dict: Query results including data, column names, and rows affected
        """
        engine = create_engine(connection_url)

        try:
            with engine.connect() as connection:
                # Start a transaction
                with connection.begin():
                    # Execute the query
                    result = connection.execute(text(sql))

                    # Handle different types of queries
                    if result.returns_rows:
                        # SELECT queries - fetch results
                        rows = result.fetchall()
                        column_names = list(result.keys()) if rows else []
                        data = [dict(row._mapping) for row in rows]

                        return {
                            "data": data,
                            "column_names": column_names,
                            "rows_affected": len(rows),
                        }
                    else:
                        # INSERT, UPDATE, DELETE, etc. - return rows affected
                        return {"data": [], "column_names": [], "rows_affected": result.rowcount}

        finally:
            engine.dispose()
