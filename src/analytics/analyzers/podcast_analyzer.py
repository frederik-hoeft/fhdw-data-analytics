from typing import Callable, List
import numpy as np
import pandas as pd
from sqlalchemy import Engine, create_engine

from analyzers.internals.analyzer_result import AnalyzerResult

class PodcastAnalyzer:
    _engine: Engine
    _theme: str
    _palette: str

    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        self._engine = create_engine(connection_string)
        self._theme = theme
        self._palette = palette

    # return a formatted time string from a number of milliseconds
    def _format_time(self, millis: float, _):
        formatted_time = pd.to_datetime(millis, unit='ms').strftime('%H:%M:%S')
        return formatted_time
    
    # return zero or one decimal places, depending on whether the number is an integer
    def _format_float(self, x: float) -> str:
        if np.isnan(x):
            return ''
        elif x == 0:
            return '0'
        elif x.is_integer():
            return '{:.0f}'.format(x)
        else:
            return '{:.1f}'.format(x)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return []