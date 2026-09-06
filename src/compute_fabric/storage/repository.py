from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compute_fabric.jobs.job_manager import Job


class JobRepository(ABC):
    @abstractmethod
    def save(self, job: "Job") -> None:
        pass

    @abstractmethod
    def get(self, job_id: str) -> "Job | None":
        pass

    @abstractmethod
    def list_all(self) -> list["Job"]:
        pass

    @abstractmethod
    def delete(self, job_id: str) -> None:
        pass
