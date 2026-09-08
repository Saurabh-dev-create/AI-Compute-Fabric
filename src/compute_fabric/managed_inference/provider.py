from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ManagedInferenceRequest:
    model_id: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.2


@dataclass(frozen=True)
class ManagedInferenceResult:
    provider: str
    model_id: str
    output_text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    request_id: str | None = None


class ManagedInferenceProvider(Protocol):
    def invoke(
        self,
        request: ManagedInferenceRequest,
    ) -> ManagedInferenceResult:
        ...
