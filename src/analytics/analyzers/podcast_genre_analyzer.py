from typing import Callable, List
from matplotlib import colors
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.analyzer_result import AnalyzerResult

class PodcastGenreAnalyzer(PodcastAnalyzer):
    def __init__(self, connection_string: str, theme: str, palette: str) -> None:
        super().__init__(connection_string, theme, palette)
    
    def capabilities(self) -> List[Callable[[], AnalyzerResult]]:
        return [
            self.genre_vs_rank,
            self.genre_vs_rank_by_region,
            self.genre_vs_presence_by_region,
            self.genre_vs_populatity_by_region
        ]
    
    # returns the average rank of each genre over all 'total' rankings (Genre = 'All') over all regions
    # Podcasts with Genre = 'Unknown' are excluded from the analysis
    def genre_vs_rank(self) -> AnalyzerResult:
        data = pd.read_sql_query(f'''
            SELECT Genre, Avg(Rank) AS AvgRank
            FROM (
                SELECT Podcasts.Genre, RankedPodcasts.Rank
                FROM RankedPodcasts
                JOIN Podcasts ON RankedPodcasts.PodcastId = Podcasts.Id
                JOIN Rankings ON RankedPodcasts.RankingId = Rankings.Id
                WHERE Podcasts.Genre <> 'Unknown' AND Rankings.Genre = 'All'
            )
            GROUP BY Genre
            ORDER BY AvgRank ASC
            ''', self._engine)
        
        def render(result: AnalyzerResult) -> Figure:
            data = result.get_data_frame()
            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            fig, ax = plt.subplots()
            # Create a bar plot
            sns.barplot(data=data, x='Genre', y='AvgRank', palette=self._palette + '_r', ax=ax)
            ax.set_xlabel('Genre')
            ax.set_ylabel('Average Rank')
            ax.set_title('Average Rank of Podcasts by Genre')
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            fig.tight_layout()
            return fig
        
        return AnalyzerResult(data, render)
    
    # returns the average rank of each genre over all 'total' rankings (Genre = 'All') clustered by region
    # Podcasts with Genre = 'Unknown' are excluded from the analysis. Only regions with genre rankings are included
    def genre_vs_rank_by_region(self) -> AnalyzerResult:
        data = pd.read_sql_query(f'''
        SELECT subquery.Genre, subquery.Country, COALESCE(AvgRank, 201) AS AvgRank
        FROM (
            SELECT DISTINCT Podcasts.Genre, Rankings.Country
            FROM Podcasts, Rankings
            WHERE Podcasts.Genre <> 'Unknown' AND Rankings.Genre <> 'All'
        ) AS subquery
        LEFT JOIN (
            SELECT Podcasts.Genre, Country, AVG(Rank) AS AvgRank
            FROM RankedPodcasts 
            INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
            INNER JOIN Podcasts ON Podcasts.Id = RankedPodcasts.PodcastId
            WHERE Rankings.Genre = "All"
            AND Podcasts.Genre <> 'Unknown' 
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
            GROUP BY Podcasts.Genre, Country
        ) AS existing_query
        ON subquery.Genre = existing_query.Genre AND subquery.Country = existing_query.Country
        ORDER BY AvgRank ASC
        ''', self._engine)
        
        def render(result: AnalyzerResult) -> Figure:
            data = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data = data.pivot_table(index='Genre', columns='Country', values='AvgRank')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Create the clustermap
            cluster_grid = sns.clustermap(data=pivot_data, vmin=abs_min, vmax=abs_max)
            
            # Access the reordered indices
            reordered_rows = cluster_grid.dendrogram_row.reordered_ind if cluster_grid.dendrogram_row is not None else pivot_data.index
            reordered_cols = cluster_grid.dendrogram_col.reordered_ind if cluster_grid.dendrogram_col is not None else pivot_data.columns
            
            # Reorder the DataFrame based on the reordered indices
            reordered_data = pivot_data.iloc[reordered_rows, reordered_cols]

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Average Rank',
                'ticks': np.linspace(abs_min, abs_max, 5)
            }

            # Create a new clustermap with the reordered data
            reordered_cluster_grid = sns.clustermap(
                data=reordered_data, 
                cmap=self._palette + '_r', 
                annot=True, 
                vmin=abs_min, 
                vmax=abs_max, 
                cbar_kws=cbar_kws, 
                fmt='.1f',
                annot_kws={'alpha': 0.75})
            reordered_cluster_grid.ax_heatmap.set_xlabel('Country')
            reordered_cluster_grid.ax_heatmap.set_ylabel('Genre')
            reordered_cluster_grid.ax_heatmap.set_title('Average Rank of Podcasts by Genre and Region')

            # Hide the row and column dendrograms
            reordered_cluster_grid.ax_row_dendrogram.set_visible(False)
            reordered_cluster_grid.ax_col_dendrogram.set_visible(False)

            # a bit stupid but this is the only way to format the annotations
            def custom_format(x):
                if np.isnan(x):
                    return ''
                elif x == 0:
                    return '0'
                elif x.is_integer():
                    return '{:.0f}'.format(x)  # Return a format specifier as a string
                else:
                    return '{:.1f}'.format(x)

            for t in reordered_cluster_grid.ax_heatmap.texts: 
                t.set_text(custom_format(float(t.get_text())))

            return reordered_cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # returns the percentage of podcast genres in the top 200 podcasts by region
    # Podcasts with Genre = 'Unknown' are included in the analysis
    def genre_vs_presence_by_region(self) -> AnalyzerResult:
        data = pd.read_sql_query(f'''
        SELECT subquery.Genre, subquery.Country, COALESCE(NumPodcasts, 0) AS NumPodcasts
        FROM (
            SELECT DISTINCT Podcasts.Genre, Rankings.Country
            FROM Podcasts, Rankings
            WHERE Rankings.Genre = 'All'
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
        ) AS subquery
        LEFT JOIN (
            SELECT Podcasts.Genre, Country, COUNT(*) AS NumPodcasts
            FROM RankedPodcasts 
            INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
            INNER JOIN Podcasts ON Podcasts.Id = RankedPodcasts.PodcastId
            WHERE Rankings.Genre = "All"
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
            GROUP BY Podcasts.Genre, Country
        ) AS existing_query
        ON subquery.Genre = existing_query.Genre AND subquery.Country = existing_query.Country
        ORDER BY NumPodcasts DESC
        ''', self._engine)
        
        # another clustermap:
        def render(result: AnalyzerResult) -> Figure:
            data = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data = data.pivot_table(index='Genre', columns='Country', values='NumPodcasts')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()

            # Create the clustermap
            cluster_grid = sns.clustermap(data=pivot_data, annot=True, vmin=abs_min, vmax=abs_max)
            
            # Access the reordered indices
            reordered_rows = cluster_grid.dendrogram_row.reordered_ind if cluster_grid.dendrogram_row is not None else pivot_data.index
            reordered_cols = cluster_grid.dendrogram_col.reordered_ind if cluster_grid.dendrogram_col is not None else pivot_data.columns
            
            # Reorder the DataFrame based on the reordered indices
            reordered_data = pivot_data.iloc[reordered_rows, reordered_cols]

            # Legend for the colorbar
            cbar_kws = {
                'label': 'Number of Podcasts',
                'ticks': np.linspace(abs_min, abs_max, 5)
            }

            # Create a new clustermap with the reordered data
            reordered_cluster_grid = sns.clustermap(data=reordered_data, cmap=self._palette + '_r', annot=True, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws)
            reordered_cluster_grid.ax_heatmap.set_xlabel('Country')
            reordered_cluster_grid.ax_heatmap.set_ylabel('Genre')
            reordered_cluster_grid.ax_heatmap.set_title('Presence of Podcast Genres in Top 200 by Region')

            # Hide the row and column dendrograms
            reordered_cluster_grid.ax_row_dendrogram.set_visible(False)
            reordered_cluster_grid.ax_col_dendrogram.set_visible(False)

            return reordered_cluster_grid.fig
        
        return AnalyzerResult(data, render)
    
    # returns the average rank of each genre over all 'total' rankings (Genre = 'All') clustered by region
    # Podcasts with Genre = 'Unknown' are excluded from the analysis. Only regions with genre rankings are included.
    # The average rank is then weighted by the number of podcasts in each genre in each region.
    def genre_vs_populatity_by_region(self) -> AnalyzerResult:
        genre_vs_rank_data = pd.read_sql_query(f'''
        SELECT subquery.Genre, subquery.Country, COALESCE(AvgRank, 201) AS AvgRank
        FROM (
            SELECT DISTINCT Podcasts.Genre, Rankings.Country
            FROM Podcasts, Rankings
            WHERE Podcasts.Genre <> 'Unknown' AND Rankings.Genre <> 'All'
        ) AS subquery
        LEFT JOIN (
            SELECT Podcasts.Genre, Country, AVG(Rank) AS AvgRank
            FROM RankedPodcasts 
            INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
            INNER JOIN Podcasts ON Podcasts.Id = RankedPodcasts.PodcastId
            WHERE Rankings.Genre = "All"
            AND Podcasts.Genre <> 'Unknown' 
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
            GROUP BY Podcasts.Genre, Country
        ) AS existing_query
        ON subquery.Genre = existing_query.Genre AND subquery.Country = existing_query.Country
        ORDER BY AvgRank ASC
        ''', self._engine)

        genre_vs_presence_data = pd.read_sql_query(f'''
        SELECT subquery.Genre, subquery.Country, COALESCE(NumPodcasts, 1) AS NumPodcasts
        FROM (
            SELECT DISTINCT Podcasts.Genre, Rankings.Country
            FROM Podcasts, Rankings
            WHERE Rankings.Genre = 'All'
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
        ) AS subquery
        LEFT JOIN (
            SELECT Podcasts.Genre, Country, COUNT(*) AS NumPodcasts
            FROM RankedPodcasts 
            INNER JOIN Rankings ON Rankings.Id = RankedPodcasts.RankingId
            INNER JOIN Podcasts ON Podcasts.Id = RankedPodcasts.PodcastId
            WHERE Rankings.Genre = "All"
            AND Rankings.Country IN (
                SELECT DISTINCT Country FROM Rankings WHERE Genre <> 'All'
            )
            GROUP BY Podcasts.Genre, Country
        ) AS existing_query
        ON subquery.Genre = existing_query.Genre AND subquery.Country = existing_query.Country
        ORDER BY NumPodcasts DESC
        ''', self._engine)

        # remove 'Unknown' genre from the data
        genre_vs_rank_data = genre_vs_rank_data[genre_vs_rank_data['Genre'] != 'Unknown']

        # merge the two dataframes on Genre and Country
        data = pd.merge(genre_vs_rank_data, genre_vs_presence_data, on=['Genre', 'Country'])

        # for every genre-country pair, calculate the weighted average rank
        # lower weighted average rank means higher popularity
        data['WeightedAvgRank'] = data['AvgRank'] / data['NumPodcasts']

        def render(result: AnalyzerResult) -> Figure:
            data = result.get_data_frame()

            # Pivot the data to create a pivot table with Genre and Country as indices
            pivot_data = data.pivot_table(index='Genre', columns='Country', values='WeightedAvgRank')

            # Set the style of seaborn
            sns.set_theme(style=self._theme)

            # Calculate the absolute minimum and maximum values of AvgRank
            abs_min = pivot_data[pivot_data >= 0].min().min()
            abs_max = pivot_data.max().max()
            
            # Create the clustermap
            cluster_grid = sns.clustermap(data=pivot_data, vmin=abs_min, vmax=abs_max)

            # Access the reordered indices
            reordered_rows = cluster_grid.dendrogram_row.reordered_ind if cluster_grid.dendrogram_row is not None else pivot_data.index
            reordered_cols = cluster_grid.dendrogram_col.reordered_ind if cluster_grid.dendrogram_col is not None else pivot_data.columns

            # Reorder the DataFrame based on the reordered indices
            reordered_data = pivot_data.iloc[reordered_rows, reordered_cols]
            
            # Legend for the colorbar
            cbar_kws = {
                'label': 'Popularity Index',
            }

            # Create a new clustermap with the reordered data
            reordered_cluster_grid = sns.clustermap(
                data=reordered_data, 
                cmap=self._palette + '_r', 
                annot=True, 
                vmin=abs_min, 
                vmax=abs_max, 
                cbar_kws=cbar_kws, 
                norm=colors.LogNorm(), 
                fmt='.1f',
                annot_kws={'alpha': 0.75})
            reordered_cluster_grid.ax_heatmap.set_xlabel('Country')
            reordered_cluster_grid.ax_heatmap.set_ylabel('Genre')
            reordered_cluster_grid.ax_heatmap.set_title('Popularity of Podcast Genres in Top 200 by Region')

            # Hide the row and column dendrograms
            reordered_cluster_grid.ax_row_dendrogram.set_visible(False)
            reordered_cluster_grid.ax_col_dendrogram.set_visible(False)

            # a bit stupid but this is the only way to format the annotations
            def custom_format(x):
                if np.isnan(x):
                    return ''
                elif x == 0:
                    return '0'
                elif x.is_integer():
                    return '{:.0f}'.format(x)  # Return a format specifier as a string
                else:
                    return '{:.1f}'.format(x)

            for t in reordered_cluster_grid.ax_heatmap.texts: 
                t.set_text(custom_format(float(t.get_text())))

            return reordered_cluster_grid.fig

        return AnalyzerResult(data, render)