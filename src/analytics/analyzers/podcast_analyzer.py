from typing import Callable, List
from sqlalchemy import Engine, create_engine

from analyzers.analyzer_result import AnalyzerResult

class PodcastAnalyzer:
    _engine: Engine
    _theme: str
    _palette: str

    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        self._engine = create_engine(connection_string)
        self._theme = theme
        self._palette = palette
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return []