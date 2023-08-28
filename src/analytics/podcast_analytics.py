from os import path
import os
from typing import Callable, List, Optional
from github.github_release import GitHubRelease
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.analyzer_result import AnalyzerResult
import tqdm
# keep these imports to allow python to do its reflection magic:
import analyzers.podcast_duration_analyzer
import analyzers.podcast_genre_analyzer

class PodcastAnalytics:
    __data_dir: str
    __output_dir: str
    __connection_string: str
    __theme: str = 'darkgrid'
    __palette: str = 'viridis'
    __github_release: GitHubRelease

    __analyzers: Optional[List[PodcastAnalyzer]] = None

    def __init__(self, data_dir: str = './data', db_file: str = 'rankings.db', output_dir: str = './rendered-results') -> None:
        self.__data_dir = data_dir
        self.__output_dir = output_dir
        self.__connection_string = 'sqlite:///' + path.abspath(path.join(data_dir, db_file))
        self.__github_release = GitHubRelease(repository_id=668823738)
    
    def __to_out_dir(self, file_name: str) -> str:
        return path.abspath(path.join(self.__output_dir, file_name))
    
    def __filename_from_capability(self, capability: Callable[[], AnalyzerResult]) -> str:
        return self.__to_out_dir('podcast_' + capability.__name__ + '.png')

    def set_style(self, theme: str, palette: str) -> None:
        self.__theme = theme
        self.__palette = palette

    def theme(self) -> str:
        return self.__theme
    
    def palette(self) -> str:
        return self.__palette

    def initialize(self) -> 'PodcastAnalytics':
        print('Initializing PodcastAnalytics...')
        self.__github_release.pull_latest_artifact('rankings.db', self.__data_dir)
        if not path.exists(self.__output_dir):
            os.makedirs(self.__output_dir)
        if self.__analyzers is None:
            analyzers: List[type] = PodcastAnalyzer.__subclasses__()
            self.__analyzers = [analyzer(self.__connection_string, self.__theme, self.__palette) for analyzer in analyzers]
        return self
    
    def run_analyzers(self, visualize: bool = False) -> None:
        if self.__analyzers is None:
            raise Exception('PodcastAnalytics has not been initialized')
        all_capabilities: List[Callable[[], AnalyzerResult]] = []
        for analyzer in self.__analyzers:
            all_capabilities.extend(analyzer.capabilities())
        print(f'Running {len(self.__analyzers)} analyzers with {len(all_capabilities)} capabilities...')
        # sort by name and then run. use tdqm to show progress
        all_capabilities.sort(key=lambda capability: capability.__name__)
        description_padding: int = len("Running ...") + max([len(capability.__name__) for capability in all_capabilities])
        with tqdm.tqdm(total=len(all_capabilities), unit='Cap') as pbar:
            for capability in all_capabilities:
                pbar.set_description(f'Running {capability.__name__}...'.ljust(description_padding))
                result = capability()
                with result.render() as rendered_result:
                    if visualize:
                        rendered_result.visualize()
                    rendered_result.save(self.__filename_from_capability(capability))
                pbar.update(1)

if __name__ == '__main__':
    spotify = PodcastAnalytics()
    spotify.set_style('darkgrid', 'viridis')
    spotify.initialize()
    spotify.run_analyzers()