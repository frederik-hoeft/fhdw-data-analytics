from typing import Callable, List, Optional
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from analyzers.models.duration_genre_classifier_model import DurationGenreClassifierModel
from analyzers.podcast_analyzer import PodcastAnalyzer

from analyzers.internals.analyzer_result import AnalyzerResult

# analyzes the average durations of podcasts in the rankings
class PodcastDurationAnalyzer(PodcastAnalyzer):
    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        super().__init__(connection_string, theme, palette)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return [
            self.duration_by_rank_cluster,
            self.duration_by_region,
            self.duration_by_genre,
            self.duration_by_genre_and_region,
            self.duration_vs_episode_count_by_genre,
            self.duration_vs_rank_by_genre,
            self.duration_by_rank,
            self.duration_vs_episode_count_by_genre_scatter
        ]
    
    # returns the average duration of podcasts in the rankings by average rank over all rankings
    # we are only interested in the rankings that contain "All" genres (i.e. the overall rankings)
    # If a podcast is not in a country-specifc top 200 ranking, it is assigned a rank of 201
    def duration_by_rank(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
        SELECT 
            Podcasts.Id,
            Podcasts.ShowName AS PodcastName,
            AllTheDurations.AvgDurationMs AS AvgDurationMs,
            AVG(AllTheRanks.Rank) AS AvgRank,
            AllTheCountryCounts.CountryCount AS CountryCount
        FROM Podcasts
        INNER JOIN (SELECT COUNT(*) AS CountryCount, RankedPodcasts.PodcastId as PodcastId
            FROM RankedPodcasts
            INNER JOIN Rankings on Rankings.Id = RankedPodcasts.RankingId
            INNER JOIN Podcasts on Podcasts.Id = RankedPodcasts.PodcastId
            WHERE Rankings.Genre = 'All'
            GROUP BY RankedPodcasts.PodcastId) 
        AS AllTheCountryCounts ON Podcasts.Id = AllTheCountryCounts.PodcastId
        INNER JOIN (SELECT Podcasts.Id as PodcastId, AVG(Episodes.DurationMs) AS AvgDurationMs
            FROM Podcasts
            INNER JOIN Episodes ON Podcasts.Id = Episodes.PodcastId
            GROUP BY PodcastId)
        AS AllTheDurations ON Podcasts.Id = AllTheDurations.PodcastId
        INNER JOIN (SELECT Podcasts.Id as PodcastId, 200 * (SELECT COUNT(*) FROM Rankings WHERE Genre = 'All') as Rank
            FROM Podcasts
            CROSS JOIN Rankings
            LEFT JOIN RankedPodcasts ON Rankings.Id = RankedPodcasts.RankingId AND RankedPodcasts.PodcastId = Podcasts.Id
            WHERE COALESCE(Rankings.Genre, 'All') = 'All' AND RankedPodcasts.PodcastId IS NULL
            UNION ALL
            SELECT Podcasts.Id as PodcastId, RankedPodcasts.Rank as Rank
            FROM Podcasts
            INNER JOIN RankedPodcasts on RankedPodcasts.PodcastId = Podcasts.Id
            INNER JOIN Rankings on Rankings.Id = RankedPodcasts.RankingId) 
        AS AllTheRanks ON Podcasts.Id = AllTheRanks.PodcastId
        GROUP BY Podcasts.Id
        ORDER BY AvgRank ASC;
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a scatter plot
            sns.scatterplot(
                x="AvgRank",  # X-axis: Average Rank
                y="AvgDurationMs",  # Y-axis: Average Duration of Episodes
                data=data,
                hue="CountryCount",  # Use different colors for each country count
                palette=self._palette + '_r',  # Color palette
                legend="auto",  # Show legend
                ax=ax
            )

            ax.set_xlabel('Average Rank')
            ax.set_ylabel('Average Duration of Episodes')
            ax.set_title('Relationship between Average Duration and Rank')
            ax.yaxis.set_major_locator(MultipleLocator(60 * 60 * 1000)) # 1 hour
            ax.yaxis.set_major_formatter(self._format_time)

            # Add legend (start at 1, end at 26, step by 5)
            legend: Legend | None = ax.get_legend()
            if legend is not None:
                legend.set_title('Number of Countries')

            fig.tight_layout()
            return fig

        return AnalyzerResult(data, render)

    # returns the average duration of podcasts in the rankings clustered grouped by clusters of 10 ranks
    # e.g. if there are 200 podcasts in the rankings, the first 10 podcasts are in cluster 0, the next 10 are in cluster 1, etc.
    # we are only interested in the rankings that contain "All" genres
    def duration_by_rank_cluster(self, cluster_size: int = 10) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query(f'''
            SELECT 
                AVG(DurationMs) as AvgDurationMs,
                -- CEILING(Rank / {cluster_size}), including upperbound as RankCluster
                (cast((Rank - 1)/{cluster_size} as int) + ((Rank - 1)/{cluster_size} > cast((Rank - 1)/{cluster_size} as int))) + 1 as RankCluster
            FROM RankedPodcasts
            INNER JOIN Episodes ON RankedPodcasts.PodcastId = Episodes.PodcastId
            INNER JOIN Rankings ON RankedPodcasts.RankingId = Rankings.Id
            WHERE Rankings.Genre = 'All'
            GROUP BY RankCluster
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.barplot(data=data, x='RankCluster', y='AvgDurationMs', palette=self._palette, ax=ax)
            ax.set_xlabel(f'Rank Cluster (Grouped by {cluster_size} Ranks)')
            ax.set_ylabel('Average Podcast Duration')
            ax.set_title('Average Podcast Duration Clustered by Rank Over All Regions')
            ax.yaxis.set_major_locator(MultipleLocator(600000))
            ax.yaxis.set_major_formatter(self._format_time)
            fig.tight_layout()
            return fig

        return AnalyzerResult(data, render)
    
    # returns the average duration of podcasts in the rankings grouped by region
    def duration_by_region(self) -> AnalyzerResult:
        data = pd.read_sql_query('''
            SELECT
                AVG(DurationMs) AS AvgDurationMs,
                Country
            FROM RankedPodcasts
            INNER JOIN Episodes ON RankedPodcasts.PodcastId = Episodes.PodcastId
            INNER JOIN Rankings ON RankedPodcasts.RankingId = Rankings.Id
            WHERE Rankings.Genre = 'All'
            GROUP BY Country
            ORDER BY AvgDurationMs DESC
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.barplot(data=data, x='Country', y='AvgDurationMs', palette=self._palette, ax=ax)
            ax.set_xlabel('Country')
            ax.set_ylabel('Average Podcast Duration')
            ax.set_title('Average Podcast Duration Clustered by Region')
            ax.yaxis.set_major_locator(MultipleLocator(600000))
            ax.yaxis.set_major_formatter(self._format_time)
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns the average duration of podcasts in the rankings grouped by Podcasts.genre (if genre is not "Unknown")
    def duration_by_genre(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT
                AVG(Episodes.DurationMs) AS AvgDurationMs,
                Podcasts.Genre AS Genre
            FROM Episodes
            INNER JOIN Podcasts ON Episodes.PodcastId = Podcasts.Id
            WHERE Podcasts.Genre <> 'Unknown'
            GROUP BY Podcasts.Genre
            ORDER BY AvgDurationMs DESC
        ''', self._engine)
        
        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.barplot(data=data, x='Genre', y='AvgDurationMs', palette=self._palette, ax=ax)
            ax.set_xlabel('Genre')
            ax.set_ylabel('Average Podcast Duration')
            ax.set_title('Average Podcast Duration Clustered by Genre')
            ax.yaxis.set_major_locator(MultipleLocator(600000))
            ax.yaxis.set_major_formatter(self._format_time)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns the average duration of podcasts in the rankings grouped by Podcasts.genre (if genre is not "Unknown")
    # and then clustered by region. Only include countries that have rankings for all genres
    def duration_by_genre_and_region(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT
                AVG(Episodes.DurationMs) AS AvgDurationMs,
                Podcasts.Genre AS Genre,
                Rankings.Country AS Country
            FROM Episodes
            INNER JOIN Podcasts ON Episodes.PodcastId = Podcasts.Id
            INNER JOIN RankedPodcasts ON Episodes.PodcastId = RankedPodcasts.PodcastId
            INNER JOIN Rankings ON RankedPodcasts.RankingId = Rankings.Id
            WHERE Podcasts.Genre <> 'Unknown' 
                AND Rankings.Country IN (
                    SELECT Country FROM (
                        SELECT Country, COUNT(*) AS Count FROM Rankings WHERE Genre <> 'All' GROUP BY Country
                    )
                )
            GROUP BY Podcasts.Genre, Rankings.Country
            ORDER BY AvgDurationMs DESC
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data: DataFrame = data.pivot_table(index='Genre', columns='Country', values='AvgDurationMs')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgDurationMs
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Avg Podcast Duration',
                'format': self._format_time,
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
                annot_kws={'alpha': 0.75})
            
            cluster_grid.ax_heatmap.set_title('Relation of Podcast Duration, Genre, and Region')
            cluster_grid.ax_heatmap.set_xlabel('Country')
            cluster_grid.ax_heatmap.set_ylabel('Genre')

            # Hide the row and column dendrograms
            cluster_grid.ax_row_dendrogram.set_visible(False)
            cluster_grid.ax_col_dendrogram.set_visible(False)

            for t in cluster_grid.ax_heatmap.texts: 
                t.set_text(self._format_time(float(t.get_text()), None))

            return cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # returns the average duration and average number of episodes of the podcasts in the rankings grouped by Podcasts.genre (if genre is not "Unknown")
    def duration_vs_episode_count_by_genre_scatter(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT 
                Genre,
                COUNT(*) AS EpisodeCount, 
                AVG(Episodes.DurationMs) AS AvgDurationMs
            FROM Episodes
            INNER JOIN Podcasts ON Episodes.PodcastId = Podcasts.Id
            WHERE Podcasts.Genre <> 'Unknown'
            GROUP BY PodcastId
        ''', self._engine)

        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a scatter plot
            sns.scatterplot(
                x="AvgDurationMs",  # X-axis: Average Duration of Episodes
                y="EpisodeCount",  # Y-axis: Average Number of Episodes
                hue="Genre",  # Use different colors for each genre
                data=data,
                palette=self._palette,  # Color palette
                s=50,  # Size of points
                ax=ax
            )
            ax.set_xlabel('Average Duration of Episodes')
            ax.set_ylabel('Number of Episodes')
            ax.set_title('Average Duration vs Number of Episodes by Genre')
            # log scale for both axes
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.xaxis.set_major_formatter(self._format_time)
            # separate legend from plot (move it to the right)
            legend: Legend | None = ax.get_legend()
            if legend is not None:
                legend.remove()
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns the average duration and average number of episodes of the podcasts in the rankings grouped by Podcasts.genre (if genre is not "Unknown")
    def duration_vs_episode_count_by_genre(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT 
                Genre, 
                AVG(EpisodeCountPerPodcast) AS AvgEpisodes,
                SUM(EpisodeCountPerPodcast * AvgDurationMsPerPodcast) / SUM(EpisodeCountPerPodcast) AS WeightedAvgDurationMs
            FROM (
                SELECT PodcastId, Genre, COUNT(*) AS EpisodeCountPerPodcast, AVG(Episodes.DurationMs) AS AvgDurationMsPerPodcast
                FROM Episodes
                INNER JOIN Podcasts ON Episodes.PodcastId = Podcasts.Id
                WHERE Podcasts.Genre <> 'Unknown'
                GROUP BY PodcastId
            )
            GROUP BY Genre;
        ''', self._engine)
        
        return DurationGenreClassifierModel(self, data)

    # returns the average duration and average rank of the podcasts in all the rankings grouped by Podcasts.genre (if genre is not "Unknown")
    def duration_vs_rank_by_genre(self) -> AnalyzerResult:
        data: DataFrame = pd.read_sql_query('''
            SELECT 
                Genre, 
                AVG(Rank) AS AvgRank,
                SUM(EpisodeCountPerPodcast * AvgDurationMsPerPodcast) / SUM(EpisodeCountPerPodcast) AS WeightedAvgDurationMs
            FROM (
                SELECT 
                    Podcasts.Genre, COUNT(*) / RankingsCount AS EpisodeCountPerPodcast, 
                    AVG(Rank) AS Rank, 
                    AVG(Episodes.DurationMs) as AvgDurationMsPerPodcast
                FROM Episodes
                INNER JOIN RankedPodcasts ON Episodes.PodcastId = RankedPodcasts.PodcastId
                INNER JOIN Rankings ON RankedPodcasts.RankingId = Rankings.Id
                INNER JOIN Podcasts ON Episodes.PodcastId = Podcasts.Id
                INNER JOIN (
                    SELECT PodcastId, COUNT(*) AS RankingsCount
                    FROM RankedPodcasts
                    GROUP BY PodcastId
                ) AS RankingsPerPodcast ON RankingsPerPodcast.PodcastId = Episodes.PodcastId
                WHERE Podcasts.Genre <> 'Unknown'
                GROUP BY Episodes.PodcastId
            )
            GROUP BY Genre;
        ''', self._engine)
        
        def render(result: AnalyzerResult) -> Figure:
            data: DataFrame = result.get_data_frame()

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a scatter plot
            sns.scatterplot(
                x="WeightedAvgDurationMs",  # X-axis: Average Duration of Episodes
                y="AvgRank",  # Y-axis: Average Rank
                hue="Genre",  # Use different colors for each genre
                data=data,
                palette=self._palette,  # Color palette
                legend="full",  # Show legend
                alpha=0.7,  # Set transparency of points
                s=100,  # Size of points
                ax=ax
            )

            # Add labels to every dot
            for i, row in data.iterrows():
                label = row['Genre']
                x = row['WeightedAvgDurationMs']
                y = row['AvgRank']
                # check if there is another label with similar coordinates (within 30s * label size and 1.5 ranks)
                # if so, move the label up or down a bit. Which direction depends on whether the label is above or below the other label
                for j, other_row in data.iterrows():
                    if i != j and abs(other_row['WeightedAvgDurationMs'] - x) < 30000 * max(len(label), len(other_row['Genre'])) and abs(other_row['AvgRank'] - y) < 1.5:
                        if y > other_row['AvgRank']:
                            y += 0.75
                        else:
                            y -= 0.75
                        break
                ax.text(x + 40000, y, label, fontsize=8, va='center')
            
            ax.set_xlabel('Average Duration of Episodes')
            ax.set_ylabel('Average Rank')
            ax.set_title('Relation of Average Duration and Rank by Genre')
            ax.xaxis.set_major_locator(MultipleLocator(600000))
            ax.xaxis.set_major_formatter(self._format_time)
            legend: Legend | None = ax.get_legend()
            if legend is not None:
                legend.remove()
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)