from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class PageData:
    url: str
    html: str = ""
    text: str = ""
    extra: dict = field(default_factory=dict)

class Detective(ABC):
    name = "unnamed"

    @abstractmethod
    def investigate(self, page):
        ...