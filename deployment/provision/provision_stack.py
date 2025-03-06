from typing import Any

from aws_cdk import Stack  # Duration,; aws_sqs as sqs,
from constructs import Construct


class ProvisionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: dict[str, Any]) -> None:
        pass
        # super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "ProvisionQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
