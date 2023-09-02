from typing import Callable, List
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.internals.analyzer_result import AnalyzerResult

class PodcastEpisodeCountAnalyzer(PodcastAnalyzer):
    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        super().__init__(connection_string, theme, palette)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return [
            self.episode_count_by_genre_and_region,
            self.episode_count_global
        ]
    
    # returns the average podcast episode count of the top 200 genres by region
    # Podcasts with Genre = 'Unknown' are excluded in the analysis
    def episode_count_by_genre_and_region(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
        SELECT subquery.genre as Genre, subquery.country as Country, (NumEpisodes/NumPublishers) as AvgNumEpisodes
        from (
            select rankings.genre, rankings.country, COUNT(Distinct ShowPublisher) as NumPublishers, COUNT(Episodes.Id) as NumEpisodes from RankedPodcasts
            inner join podcasts on Podcasts.Id = RankedPodcasts.PodcastId
            inner join rankings on Rankings.Id = RankedPodcasts.RankingId
            inner join Episodes on Episodes.PodcastId = Podcasts.Id
            where rankings.Genre != 'All'
            group by rankings.genre, rankings.Country) as subquery
        order by AvgNumEpisodes DESC
        ''', self._engine)
        
        # another clustermap:
        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data: DataFrame = data.pivot_table(index='Genre', columns='Country', values='AvgNumEpisodes')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Average Number of Episodes',
                'ticks': np.linspace(abs_min, abs_max, 5)
            }

            # Create a clustermap with the data
            cluster_grid = sns.clustermap(data=pivot_data, cmap=self._palette + '_r', annot=True, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws, fmt='g')
            cluster_grid.ax_heatmap.set_xlabel('Country')
            cluster_grid.ax_heatmap.set_ylabel('Genre')
            cluster_grid.ax_heatmap.set_title('Average Podcast Episode Count of Top 200 Genres by Region')

            # Hide the row and column dendrograms
            cluster_grid.ax_row_dendrogram.set_visible(False)
            cluster_grid.ax_col_dendrogram.set_visible(False)

            return cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # returns a probability distribution of the average podcast episode count
    def episode_count_global(self) -> AnalyzerResult:
        data = pd.read_sql_query('''
        SELECT subquery.Genre as Genre, subquery.Country as Country, (NumEpisodes/NumPublishers) as AvgNumEpisodes
        from (
            select rankings.genre, rankings.country, COUNT(Distinct ShowPublisher) as NumPublishers, COUNT(Episodes.Id) as NumEpisodes from RankedPodcasts
            inner join podcasts on Podcasts.Id = RankedPodcasts.PodcastId
            inner join rankings on Rankings.Id = RankedPodcasts.RankingId
            inner join Episodes on Episodes.PodcastId = Podcasts.Id
            where rankings.Genre != 'All'
            group by rankings.genre, rankings.Country) as subquery
        order by AvgNumEpisodes DESC
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            # sns.barplot(data=data, x='AvgNumEpisodes', y='AvgNumEpisodes', palette=self._palette, ax=ax)
            sns.displot(data=data, x="AvgNumEpisodes", kind="kde") # <- ist irgendwie leer?
            ax.set_xlabel('Average Episode Count')
            ax.set_ylabel('Probability')
            ax.set_title('Average Podcast Episode Count')
            # ax.yaxis.set_major_locator(MultipleLocator(600000))
            # ax.yaxis.set_major_formatter(self._format_time)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)