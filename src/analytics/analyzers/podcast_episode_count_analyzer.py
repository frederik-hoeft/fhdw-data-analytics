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
            self.episode_count_distribution,
            self.episode_count_distribution_top_200
        ]
    
    # returns the average podcast episode count of the top 200 genres by region
    # Podcasts with Genre = 'Unknown' are excluded in the analysis
    def episode_count_by_genre_and_region(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
        SELECT 
            subquery.genre as Genre, 
            subquery.country as Country, 
            (NumEpisodes/NumPublishers) as AvgNumEpisodes
        from (
            select 
                rankings.genre, 
                rankings.country, 
                COUNT(Distinct Podcasts.Id) as NumPublishers, 
                COUNT(Episodes.Id) as NumEpisodes from RankedPodcasts
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
    def episode_count_distribution_top_200(self) -> AnalyzerResult:
        data = pd.read_sql_query('''
        WITH AvgEpisodesDistribution AS (
            SELECT
                subquery.Genre AS Genre,
                subquery.Country AS Country,
                ROUND((NumEpisodes / NumPublishers) / 5) * 5 AS RoundedAvgNumEpisodes
            FROM (
                SELECT
                    rankings.genre,
                    rankings.country,
                    COUNT(DISTINCT ShowPublisher) AS NumPublishers,
                    COUNT(Episodes.Id) AS NumEpisodes
                FROM RankedPodcasts
                INNER JOIN Podcasts ON Podcasts.Id = RankedPodcasts.PodcastId
                INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
                INNER JOIN Episodes ON Episodes.PodcastId = Podcasts.Id
                WHERE rankings.Genre != 'All'
                GROUP BY rankings.genre, rankings.Country
            ) AS subquery
        )

        SELECT
            RoundedAvgNumEpisodes AS AvgNumEpisodes,
            COUNT(*) AS Frequency,
            1.0 * COUNT(*) / (SELECT COUNT(*) FROM AvgEpisodesDistribution) AS Probability
        FROM AvgEpisodesDistribution
        GROUP BY AvgNumEpisodes
        ORDER BY AvgNumEpisodes;
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.lineplot(data=data, x='AvgNumEpisodes', y='Probability', ax=ax)
            ax.set_xlabel('Average Episode Count')
            ax.set_ylabel('Probability')
            ax.set_title('Average Podcast Episode Count')
            # ax.yaxis.set_major_locator(MultipleLocator(600000))
            # ax.yaxis.set_major_formatter(self._format_time)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns a distribution of the average podcast episode count
    def episode_count_distribution(self) -> AnalyzerResult:
        data = pd.read_sql_query('''
        SELECT 
            COUNT(*) AS Frequency,
            EpisodeCount
        FROM (
            SELECT
                Podcasts.Id AS PodcastId,
                COUNT(Episodes.Id) AS EpisodeCount
            FROM Podcasts
            INNER JOIN Episodes ON Episodes.PodcastId = Podcasts.Id
            GROUP BY Podcasts.Id
        )
        GROUP BY EpisodeCount
        ORDER BY EpisodeCount;
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.kdeplot(data=data, x='EpisodeCount', ax=ax)
            ax.set_xlabel('Episode Count')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Podcast Episode Counts')
            # add a vertical line at the mean
            ax.axvline(data['EpisodeCount'].mean(), color='red', linestyle='dashed', linewidth=1)
            # add corresponding labels with the mean value
            ax.text(data['EpisodeCount'].mean() + 1, 0.0005, 'Mean: {:.2f}'.format(data['EpisodeCount'].mean()))
            # hide negative values on the x-axis
            ax.set_xlim(left=0)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)