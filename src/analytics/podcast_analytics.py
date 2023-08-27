from os import path
import os
from typing import Callable, List
from rankings_db_updater import RankingsDBUpdater
from analyzers.podcast_duration_analyzer import PodcastDurationAnalyzer
from analyzers.analyzer_result import AnalyzerResult

class PodcastAnalytics:
    __data_dir: str
    __output_dir: str
    __connection_string: str
    __theme: str = 'darkgrid'
    __palette: str = 'viridis'

    def __init__(self, data_dir: str = './data', db_file: str = 'rankings.db', output_dir: str = './rendered-results') -> None:
        self.__data_dir = data_dir
        self.__output_dir = output_dir
        self.__connection_string = 'sqlite:///' + path.abspath(path.join(data_dir, db_file))
    
    def __to_out_dir(self, file_name: str) -> str:
        return path.abspath(path.join(self.__output_dir, file_name))
    
    def __filename_from_capability(self, capability: Callable[[None], AnalyzerResult]) -> str:
        return self.__to_out_dir('podcast_' + capability.__name__ + '.png')

    def set_style(self, theme: str = 'darkgrid', palette: str = 'viridis') -> None:
        self.__theme = theme
        self.__palette = palette

    def theme(self) -> str:
        return self.__theme
    
    def palette(self) -> str:
        return self.__palette

    def initialize(self) -> 'PodcastAnalytics':
        RankingsDBUpdater.update_rankings_db(self.__data_dir)
        if not path.exists(self.__output_dir):
            os.makedirs(self.__output_dir)
        return self

    def analyze_durations(self, visualize: bool = False) -> None:
        analyzer = PodcastDurationAnalyzer(self.__connection_string, self.__theme, self.__palette)
        capabilities: List[Callable[[None], AnalyzerResult]] = analyzer.capabilities()
        for capability in capabilities:
            out_name: str = self.__filename_from_capability(capability)
            print(f'Rendering {out_name}...')
            result: AnalyzerResult = capability()
            with result.render() as rendered_result:
                if visualize:
                    rendered_result.visualize()
                rendered_result.save(out_name)

if __name__ == '__main__':
    spotify = PodcastAnalytics().initialize()
    spotify.analyze_durations()