from dataclasses import dataclass

from .config import Settings
from .content import ContentRegistry
from .llm.base import LabGenerator, TutorModel


@dataclass
class Services:
    settings: Settings
    registry: ContentRegistry
    generator: LabGenerator
    tutor: TutorModel
