from typing import Callable, List
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.internals.analyzer_result import AnalyzerResult

class PodcastEpisodeTimeAnalyzer(PodcastAnalyzer):
    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        super().__init__(connection_string, theme, palette)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return [
            self.episode_time_by_genre_and_region,
            self.episode_time_global
        ]
    
    # returns the average time passed in Months since the release of the first episode in the top 200 genres by region
    # Podcasts with Genre = 'Unknown' are excluded in the analysis
    def episode_time_by_genre_and_region(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
        select CAST(avg(TimePassed)/365*12 AS INT) as AvgTimePassed, subquery.Genre, subquery.Country, subquery.Rank
        from (
            select CAST((JULIANDAY('now') - JULIANDAY(Episodes.ReleaseDate)) as INT) as TimePassed, Rankings.Genre, Rankings.Country, RankedPodcasts.Rank from Episodes
            inner join Podcasts on Podcasts.Id = Episodes.PodcastId
            inner join RankedPodcasts on RankedPodcasts.PodcastId = Podcasts.Id
            inner join Rankings on Rankings.Id = RankedPodcasts.RankingId
            where Rankings.Genre != 'All') as subquery
        group by subquery.Genre, subquery.Country
        order by AvgTimePassed DESC
        ''', self._engine)
        
        # another clustermap:
        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data: DataFrame = data.pivot_table(index='Genre', columns='Country', values='AvgTimePassed')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Time in Months',
                'ticks': np.linspace(abs_min, abs_max, 5)
            }

            # Create a clustermap with the data
            cluster_grid = sns.clustermap(data=pivot_data, cmap=self._palette + '_r', annot=True, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws, fmt='g')
            cluster_grid.ax_heatmap.set_xlabel('Country')
            cluster_grid.ax_heatmap.set_ylabel('Genre')
            cluster_grid.ax_heatmap.set_title('Average Time passed since First Podcast Episode in the Top 200 Genres by Region')

            # Hide the row and column dendrograms
            cluster_grid.ax_row_dendrogram.set_visible(False)
            cluster_grid.ax_col_dendrogram.set_visible(False)

            return cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # returns a probability distribution of the average time passed since the first podcast episode
    def episode_time_global(self) -> AnalyzerResult:
        data = pd.read_sql_query('''
        WITH AvgTimePassedDistribution AS (
            SELECT
                subquery.Genre AS Genre,
                subquery.Country AS Country,
                CAST(AVG(subquery.TimePassed) / 365 * 12 as INT) AS AvgTimePassed
            FROM (
                SELECT
                    CAST((JULIANDAY('now') - JULIANDAY(Episodes.ReleaseDate)) AS INT) AS TimePassed,
                    Rankings.Genre,
                    Rankings.Country
                FROM Episodes
                INNER JOIN Podcasts ON Podcasts.Id = Episodes.PodcastId
                INNER JOIN RankedPodcasts ON RankedPodcasts.PodcastId = Podcasts.Id
                INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
                WHERE Rankings.Genre != 'All'
            ) AS subquery
            GROUP BY subquery.Genre, subquery.Country
        )

        SELECT
            Genre,
            Country,
            AvgTimePassed,
            COUNT(*) AS Frequency,
            1.0 * COUNT(*) / (SELECT COUNT(*) FROM AvgTimePassedDistribution) AS Probability
        FROM AvgTimePassedDistribution
        GROUP BY AvgTimePassed
        ORDER BY AvgTimePassed DESC;
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.lineplot(data=data, x='AvgTimePassed', y='Probability', palette=self._palette + '_r', ax=ax)
            ax.set_xlabel('Average Time Passed')
            ax.set_ylabel('Probability')
            ax.set_title('Average Time Passed since First Podcast Episode')
            # ax.yaxis.set_major_locator(MultipleLocator(600000))
            # ax.yaxis.set_major_formatter(self._format_time)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)