from typing import Any

from compute_fabric.managed_inference.provider import (
    ManagedInferenceRequest,
    ManagedInferenceResult,
)


class BedrockProvider:
    def __init__(self, client: Any) -> None:
        self.client = client

    def invoke(
        self,
        request: ManagedInferenceRequest,
    ) -> ManagedInferenceResult:
        response = self.client.converse(
            modelId=request.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": request.prompt,
                        },
                    ],
                },
            ],
            inferenceConfig={
                "maxTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        )

        output_text = response["output"]["message"]["content"][0]["text"]

        usage = response.get("usage", {})
        metadata = response.get("ResponseMetadata", {})

        input_tokens = usage.get("inputTokens")
        output_tokens = usage.get("outputTokens")

        total_tokens = (
            input_tokens + output_tokens
            if input_tokens is not None and output_tokens is not None
            else None
        )

        return ManagedInferenceResult(
            provider="bedrock",
            model_id=request.model_id,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            request_id=metadata.get("RequestId"),
        )
