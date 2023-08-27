from pandas import DataFrame
from contextlib import contextmanager
import matplotlib.pyplot as plt
from typing import Optional

class AnalyzerResult:
    __data_frame: DataFrame
    __render: callable

    def __init__(self, data_frame: DataFrame, render: callable) -> None:
        self.__data_frame = data_frame
        self.__render = render

    def get_data_frame(self) -> DataFrame:
        return self.__data_frame
    
    @contextmanager
    def render(self: 'AnalyzerResult') -> 'RenderedAnalyzerResult':
        # uses seaborn to render the plot
        plot: Optional[plt.Figure] = self.__render(self)
        yield RenderedAnalyzerResult(plot)
        plt.close(plot)

class RenderedAnalyzerResult:
    __plot: Optional[plt.Figure]

    def __init__(self, plot: Optional[plt.Figure] = None) -> None:
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