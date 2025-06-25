from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class EvaluationTestCase:
    """Represent a single input-output pair for evaluation."""
    prompt: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseEvaluationDataset(ABC):
    """Abstract base class for all evaluation datasets."""
    def __init__(self, data: List[EvaluationTestCase]):
        self._data = data
    
    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __getitem__(self, idx: int) -> EvaluationTestCase:
        pass

    @abstractmethod
    def to_dataframe(self):
        """Convert the dataset to a dataframe."""
        pass
