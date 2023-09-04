import matplotlib as mpl
from matplotlib.figure import Figure
from pandas import DataFrame
from contextlib import contextmanager
import matplotlib.pyplot as plt
from typing import Any, Callable, Generator, List, Optional, Tuple

class AnalyzerResult:
    __data_frame: DataFrame
    __render: Callable[['AnalyzerResult'], Figure]
    __model: Optional['AnalyzerResultModel'] = None

    def __init__(self, data_frame: DataFrame, render: Callable[['AnalyzerResult'], Figure]) -> None:
        self.__data_frame = data_frame
        self.__render = render
        if mpl.is_interactive():
            mpl.interactive(False)

    def get_data_frame(self) -> DataFrame:
        return self.__data_frame
    
    def get_model(self) -> Optional['AnalyzerResultModel']:
        return self.__model
    
    def set_model(self, model: 'AnalyzerResultModel') -> None:
        self.__model = model
    
    @contextmanager
    def render(self: 'AnalyzerResult') -> Generator['RenderedAnalyzerResult', Any, Any]:
        # uses seaborn to render the plot
        plot: Figure = self.__render(self)
        yield RenderedAnalyzerResult(plot)
        plt.close(plot)
    

class AnalyzerResultModel(AnalyzerResult):
    _model_visualizations: List[Callable[[AnalyzerResult], Figure]]
    _theme: str
    _palette: str

    def __init__(self, data_frame: DataFrame, theme: str, palette: str, render: Callable[['AnalyzerResult'], Figure]) -> None:
        super().__init__(data_frame, render)
        self._theme = theme
        self._palette = palette
        self._model_visualizations = []
        super().set_model(self)

    def _set_model_visualizations(self, model_visualizations: List[Callable[[AnalyzerResult], Figure]]) -> None:
        self._model_visualizations = model_visualizations
    
    def get_visualizations(self) -> List[Tuple[AnalyzerResult, str]]:
        visualizations: List[Tuple[AnalyzerResult, str]] = []
        for visualization in self._model_visualizations:
            visualizations.append((AnalyzerResult(self.get_data_frame(), visualization), visualization.__name__))
        return visualizations

class RenderedAnalyzerResult:
    __plot: Optional[Figure]

    def __init__(self, plot: Figure) -> None:
        self.__plot = plot

    def visualize(self) -> None:
        if self.__plot is not None:
            plt.show()

    def save(self, file_name: str) -> None:
        if self.__plot is not None:
            self.__plot.savefig(file_name, dpi=300)

    def __enter__(self) -> 'RenderedAnalyzerResult':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.__plot is not None:
            plt.close(self.__plot)
            self.__plot = None