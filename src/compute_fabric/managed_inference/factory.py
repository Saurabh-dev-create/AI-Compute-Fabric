from collections.abc import Mapping

import boto3

from compute_fabric.managed_inference.bedrock_provider import BedrockProvider
from compute_fabric.managed_inference.service import ManagedInferenceService


def create_managed_inference_service(
    environment: Mapping[str, str],
) -> ManagedInferenceService:
    region = environment.get(
        "AWS_REGION",
        environment.get("AWS_DEFAULT_REGION", "ap-south-1"),
    ).strip()

    if not region:
        raise RuntimeError("AWS region must not be empty")

    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=region,
    )

    return ManagedInferenceService(
        providers={
            "bedrock": BedrockProvider(bedrock_client),
        },
    )
