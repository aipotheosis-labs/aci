from collections.abc import Generator

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

from aci.common.logging_setup import get_logger
from aci.server.config import ENVIRONMENT, OPENSEARCH_AWS_REGION, OPENSEARCH_HOST, OPENSEARCH_PORT


def yield_opensearch_client() -> Generator[OpenSearch, None, None]:
    """
    Creates and yields an OpenSearch client configured with either HTTP basic auth (local) or IAM auth (production).
    """
    client = None
    try:
        if ENVIRONMENT == "local":
            # Create OpenSearch client with HTTP basic auth for local development
            client = OpenSearch(
                hosts=[{"host": "opensearch", "port": 9200}],
                http_auth=("admin", "admin"),
                http_compress=True,  # enables gzip compression for request bodies
                use_ssl=False,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                connection_class=RequestsHttpConnection,
            )
        else:
            # Create OpenSearch client with IAM auth for production
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, OPENSEARCH_AWS_REGION, "es")

            client = OpenSearch(
                hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20,
            )

        yield client
    except Exception as e:
        get_logger(__name__).error(f"Error creating OpenSearch client: {e!s}")
        raise
    finally:
        if client:
            client.close()
