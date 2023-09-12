from typing import Callable, List
from matplotlib.dates import YearLocator
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from analyzers.models.upload_frequency_model import UploadFrequencyModel
from analyzers.internals.binary_search_wrapper import BinarySearchWrapper
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.internals.analyzer_result import AnalyzerResult

class PodcastUploadAnalyzer(PodcastAnalyzer):
    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        super().__init__(connection_string, theme, palette)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return [
            self.upload_absolute_frequency,
            self.upload_frequency_by_day_of_week,
            self.upload_frequency_by_day_of_week_by_region,
            self.upload_relative_frequency
        ]
    
    def upload_frequency_by_day_of_week(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT
                COUNT(*) AS Uploads,
                DayOfWeek AS DayOfWeek,
                CASE DayOfWeek
                    WHEN '0' THEN 'Sun'
                    WHEN '1' THEN 'Mon'
                    WHEN '2' THEN 'Tue'
                    WHEN '3' THEN 'Wed'
                    WHEN '4' THEN 'Thu'
                    WHEN '5' THEN 'Fri'
                    WHEN '6' THEN 'Sat'
                END AS DayOfWeekName
            FROM Episodes
            INNER JOIN (
                SELECT Id as EpisodeId, strftime('%w', ReleaseDate) AS DayOfWeek
                FROM Episodes
            ) AS DayOfWeek ON Episodes.Id = DayOfWeek.EpisodeId
            WHERE ReleaseDatePrecision = 'day'
            GROUP BY DayOfWeek
            ORDER BY DayOfWeek ASC
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots() 
            sns.barplot(data=data, x='DayOfWeekName', y='Uploads', palette=self._palette + '_r', ax=ax)
            ax.set_title('Uploads per Day of Week')
            ax.set_xlabel('Day of Week')
            ax.set_ylabel('Uploads')
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # plots the number of uploads per day over time between the given years
    def upload_absolute_frequency(self, year_lower_bound: int = 2013, year_upper_bound: int = 2023) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
            SELECT
                COUNT(*) AS Uploads,
                ReleaseDate AS Date
            FROM Episodes
            WHERE ReleaseDatePrecision = 'day'
                AND ReleaseDate >= '{year_lower_bound}-01-01'
                AND ReleaseDate <= '{year_upper_bound}-12-31'
            GROUP BY ReleaseDate
            ORDER BY ReleaseDate ASC
        ''', self._engine)

        data['Date'] = pd.to_datetime(data['Date'])
        
        # Create a categorical column based on the year of the Date column
        data['Year'] = data['Date'].dt.year.astype(str)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots() 
            sns.lineplot(data=data, x='Date', y='Uploads', hue='Year', palette=self._palette + '_r', ax=ax)
            ax.set_title('Uploads per Day')
            ax.set_xlabel('Year')
            ax.set_ylabel('Uploads')
            ax.xaxis.set_major_locator(YearLocator(base=1))
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    def upload_frequency_by_day_of_week_by_region(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            WITH UploadsPerCountryPerDay AS (
                SELECT COUNT(DISTINCT e.Id) as Uploads,
                    r.Country,
                    DayOfWeek AS DayOfWeek,
                    CASE DayOfWeek
                        WHEN '0' THEN 'Sunday'
                        WHEN '1' THEN 'Monday'
                        WHEN '2' THEN 'Tuesday'
                        WHEN '3' THEN 'Wednesday'
                        WHEN '4' THEN 'Thursday'
                        WHEN '5' THEN 'Friday'
                        WHEN '6' THEN 'Saturday'
                    END AS DayOfWeekName
                FROM Episodes e
                INNER JOIN (
                    SELECT Id as EpisodeId, strftime('%w', e2.ReleaseDate) AS DayOfWeek
                    FROM Episodes e2
                ) AS DayOfWeek ON e.Id = DayOfWeek.EpisodeId
                INNER JOIN Podcasts p ON p.Id = e.PodcastId
                INNER JOIN RankedPodcasts rp ON rp.PodcastId = p.Id
                INNER JOIN Rankings r ON r.Id = rp.RankingId
                WHERE e.ReleaseDatePrecision = 'day'
                GROUP BY Country, DayOfWeek), 
            UploadsPerCountry AS (
                SELECT COUNT(DISTINCT e.Id) as Uploads,
                    r.Country
                FROM Episodes e
                INNER JOIN Podcasts p ON p.Id = e.PodcastId
                INNER JOIN RankedPodcasts rp ON rp.PodcastId = p.Id
                INNER JOIN Rankings r ON r.Id = rp.RankingId
                WHERE e.ReleaseDatePrecision = 'day'
                GROUP BY Country)
            SELECT 
                CAST(ucd.Uploads AS FLOAT) / uc.Uploads * 100 AS Uploads,
                ucd.Country,
                ucd.DayOfWeekName
            FROM UploadsPerCountryPerDay ucd
            INNER JOIN UploadsPerCountry uc ON ucd.Country = uc.Country;
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Pivot the data to create a pivot table with DayOfWeekName as the index, Country as the columns, and Uploads as the values
            pivot_data: DataFrame = data.pivot_table(index='Country', columns='DayOfWeekName', values='Uploads')
            # Reindex the columns to be in the correct order
            pivot_data = pivot_data.reindex(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], axis='columns')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Average Uploads',
                'ticks': np.linspace(abs_min, abs_max, 5)
            }

            # Create a clustermap with the data
            cluster_grid = sns.clustermap(
                data=pivot_data, 
                cmap=self._palette + '_r', 
                annot=True, 
                vmin=abs_min, 
                vmax=abs_max, 
                cbar_kws=cbar_kws, 
                col_cluster=False,
                fmt='.1f',
                annot_kws={'alpha': 0.75})
            cluster_grid.ax_heatmap.set_xlabel('DayOfWeekName')
            cluster_grid.ax_heatmap.set_ylabel('Country')
            cluster_grid.ax_heatmap.set_title('Uploads per Day of Week by Country')

            # Hide the row and column dendrograms
            cluster_grid.ax_row_dendrogram.set_visible(False)
            cluster_grid.ax_col_dendrogram.set_visible(False)

            # Rotate the x-axis labels to be horizontal
            cluster_grid.ax_heatmap.set_yticklabels(cluster_grid.ax_heatmap.get_yticklabels(), rotation=0)

            def format_float_percentage(value: float) -> str:
                return self._format_float(value) + '%'

            for t in cluster_grid.ax_heatmap.texts: 
                t.set_text(format_float_percentage(float(t.get_text())))

            return cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # plots the relative number of uploads per day over time between the given years
    # relative number of uploads is defined as the number of uploads on a given day divided by the number of 
    # podcasts that have released at least one episode up to and including that day
    def upload_relative_frequency(self, year_lower_bound: int = 2013, year_upper_bound: int = 2023) -> AnalyzerResult:
        # get absolute frequency data with unix timestamps for each date
        data: DataFrame = pd.read_sql_query(f'''
            SELECT
                COUNT(*) AS Uploads,
                ReleaseDate AS Date,
                CAST(strftime('%s', ReleaseDate) AS INT) AS DateEpoch
            FROM Episodes
            WHERE ReleaseDatePrecision = 'day'
                AND ReleaseDate >= '{year_lower_bound}-01-01'
                AND ReleaseDate <= '{year_upper_bound}-12-31'
            GROUP BY ReleaseDate
            ORDER BY ReleaseDate ASC
        ''', self._engine)

        # get the first release date for each podcast as a unix timestamp
        # ordered ascending by the first release date
        first_releases: DataFrame = pd.read_sql_query(f'''
            SELECT CAST(strftime('%s', MIN(ReleaseDate)) AS INT) AS FirstReleaseEpoch
            FROM Episodes
            GROUP BY PodcastId
            ORDER BY FirstReleaseEpoch ASC
        ''', self._engine)
        
        # extract the first release dates as a list
        ordered_first_releases: List[int] = first_releases['FirstReleaseEpoch'].tolist()
        # create a binary search wrapper for the first release dates
        bsw: BinarySearchWrapper = BinarySearchWrapper(ordered_first_releases)
        # add a column to the data with the position of the first release date for each podcast
        # this is the number of podcasts that have released at least one episode up to and including the date
        data['PodcastCount'] = data['DateEpoch'].apply(lambda date_ts: bsw.position_of_value_or_one_below(date_ts))
        # ffs this took way too long, but here we go. fucking finally :P
        data['RelativeUploads'] = data['Uploads'] / data['PodcastCount']

        # prepare visualization data
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Create a categorical column based on the year of the Date column
        data['Year'] = data['Date'].dt.year.astype(str)
        
        return UploadFrequencyModel(self, data)