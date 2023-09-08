from typing import Callable, List
from matplotlib.dates import YearLocator
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
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
            self.episode_time_distribution,
            self.episode_time_distribution_genre_all
        ]
    
    # returns the average time passed in Months since the release of the first episode in the top 200 genres by region
    # Podcasts with Genre = 'Unknown' are excluded in the analysis
    def episode_time_by_genre_and_region(self) -> AnalyzerResult:
        newestDateData: DataFrame = pd.read_sql_query(f'''
        select max(ReleaseDate)
        from Episodes
        ''', self._engine)

        newestDate = newestDateData.iloc[0].values[0]

        data: DataFrame = pd.read_sql_query(f'''
        select 
            round(avg(TimePassed)/365, 2) as AvgTimePassed, 
            subquery.Genre, 
            subquery.Country, 
            subquery.Rank
        from (
            select CAST((JULIANDAY('{newestDate}') - JULIANDAY(Episodes.ReleaseDate)) as INT) as TimePassed, Rankings.Genre, Rankings.Country, RankedPodcasts.Rank from Episodes
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
                'label': 'Time in Years',
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
    
    # returns a distribution of the release months of the number of first podcast episodes released every month
    def episode_time_distribution(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
            SELECT FirstReleaseMonth AS Date, COUNT(*) AS Uploads 
            FROM (
                SELECT 
                    strftime('%Y-%m', MIN(ReleaseDate)) AS FirstReleaseMonth
                FROM Episodes
                GROUP BY PodcastId)
            GROUP BY Date
            ORDER BY Date ASC
        ''', self._engine)

        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m')

        # calculate the time passed since the the latest entry in the data and all other entries
        # (How much time has passed since the first podcast episode was released and 'now' (the latest entry in the data))
        data['Date'] = (data['Date'].max() - data['Date']).dt.days / 365.0

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.kdeplot(data=data, x='Date', ax=ax)
            ax.set_xlabel('Years Passed since First Release')
            ax.set_ylabel('Number of First Releases')
            ax.set_title('Number of First Podcast Episodes by Years Passed since First Release')
            # add a vertical line at the mean
            ax.axvline(data['Date'].mean(), color='red', linestyle='dashed', linewidth=1)
            # add corresponding labels with the mean value
            ax.text(data['Date'].mean() + 1, 0.0005, 'Mean: {:.2f} years'.format(data['Date'].mean()))
            # hide negative values on the x-axis
            ax.set_xlim(left=0)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns a distribution of the release months of the number of first podcast episodes released every month
    def episode_time_distribution_genre_all(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
        SELECT FirstReleaseMonth AS Date, COUNT(*) AS Uploads 
        FROM (
            SELECT 
                strftime('%Y-%m', MIN(ReleaseDate)) AS FirstReleaseMonth
            FROM Episodes
            inner join Podcasts on Episodes.PodcastId = Podcasts.Id
            inner join RankedPodcasts on RankedPodcasts.PodcastId = Podcasts.Id
            inner join Rankings on Rankings.Id = RankedPodcasts.RankingId
            where Rankings.Genre = "All"
            GROUP BY Episodes.PodcastId)
        GROUP BY Date
        ORDER BY Date ASC
        ''', self._engine)

        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m')

        # calculate the time passed since the the latest entry in the data and all other entries
        # (How much time has passed since the first podcast episode was released and 'now' (the latest entry in the data))
        data['Date'] = (data['Date'].max() - data['Date']).dt.days / 365.0

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.kdeplot(data=data, x='Date', ax=ax)
            ax.set_xlabel('Years Passed')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of First Podcast Episodes by Years Passed since First Release')
            # add a vertical line at the mean
            ax.axvline(data['Date'].mean(), color='red', linestyle='dashed', linewidth=1)
            # add corresponding labels with the mean value
            ax.text(data['Date'].mean() + 1, 0.0005, 'Mean: {:.2f} years'.format(data['Date'].mean()))
            # hide negative values on the x-axis
            ax.set_xlim(left=0)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)