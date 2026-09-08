import pytest

from compute_fabric.managed_inference.bedrock_provider import BedrockProvider
from compute_fabric.managed_inference.provider import ManagedInferenceRequest
from compute_fabric.managed_inference.service import ManagedInferenceService


class FakeBedrockClient:
    def __init__(self) -> None:
        self.request = None

    def converse(self, **kwargs):
        self.request = kwargs

        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": "Managed inference response",
                        },
                    ],
                },
            },
            "usage": {
                "inputTokens": 12,
                "outputTokens": 8,
            },
            "ResponseMetadata": {
                "RequestId": "bedrock-request-001",
            },
        }


def test_bedrock_provider_invokes_converse_api() -> None:
    client = FakeBedrockClient()
    provider = BedrockProvider(client)

    request = ManagedInferenceRequest(
        model_id="example-model",
        prompt="Explain GPU scheduling.",
        max_tokens=128,
        temperature=0.1,
    )

    result = provider.invoke(request)

    assert client.request == {
        "modelId": "example-model",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Explain GPU scheduling.",
                    },
                ],
            },
        ],
        "inferenceConfig": {
            "maxTokens": 128,
            "temperature": 0.1,
        },
    }

    assert result.provider == "bedrock"
    assert result.model_id == "example-model"
    assert result.output_text == "Managed inference response"
    assert result.input_tokens == 12
    assert result.output_tokens == 8
    assert result.total_tokens == 20
    assert result.request_id == "bedrock-request-001"


def test_managed_inference_service_routes_to_provider() -> None:
    provider = BedrockProvider(FakeBedrockClient())

    service = ManagedInferenceService(
        providers={
            "bedrock": provider,
        },
    )

    result = service.invoke(
        "bedrock",
        ManagedInferenceRequest(
            model_id="example-model",
            prompt="Hello",
        ),
    )

    assert result.provider == "bedrock"
    assert result.output_text == "Managed inference response"


def test_managed_inference_service_rejects_unknown_provider() -> None:
    service = ManagedInferenceService(providers={})

    with pytest.raises(
        ValueError,
        match="Unsupported managed inference provider: unknown",
    ):
        service.invoke(
            "unknown",
            ManagedInferenceRequest(
                model_id="example-model",
                prompt="Hello",
            ),
        )


def test_factory_creates_bedrock_managed_inference_service(
    monkeypatch,
) -> None:
    from compute_fabric.managed_inference import factory

    captured = {}

    class FakeBoto3:
        @staticmethod
        def client(service_name, region_name):
            captured["service_name"] = service_name
            captured["region_name"] = region_name
            return FakeBedrockClient()

    monkeypatch.setattr(factory, "boto3", FakeBoto3)

    service = factory.create_managed_inference_service(
        {
            "AWS_REGION": "ap-south-1",
        }
    )

    result = service.invoke(
        "bedrock",
        ManagedInferenceRequest(
            model_id="example-model",
            prompt="Hello",
        ),
    )

    assert captured["service_name"] == "bedrock-runtime"
    assert captured["region_name"] == "ap-south-1"
    assert result.provider == "bedrock"
