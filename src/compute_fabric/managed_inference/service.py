from collections.abc import Mapping

from compute_fabric.managed_inference.provider import (
    ManagedInferenceProvider,
    ManagedInferenceRequest,
    ManagedInferenceResult,
)


class ManagedInferenceService:
    def __init__(
        self,
        providers: Mapping[str, ManagedInferenceProvider],
    ) -> None:
        self.providers = providers

    def invoke(
        self,
        provider_name: str,
        request: ManagedInferenceRequest,
    ) -> ManagedInferenceResult:
        provider = self.providers.get(provider_name)

        if provider is None:
            raise ValueError(
                f"Unsupported managed inference provider: {provider_name}"
            )

        return provider.invoke(request)
