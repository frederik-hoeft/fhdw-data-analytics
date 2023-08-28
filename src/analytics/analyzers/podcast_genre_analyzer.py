'''
rankings.db database schema:
CREATE TABLE IF NOT EXISTS "DataSets" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_DataSets" PRIMARY KEY AUTOINCREMENT,
    "CollectedAt" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "Episodes" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Episodes" PRIMARY KEY AUTOINCREMENT,
    "DurationMs" INTEGER NOT NULL,
    "Explicit" INTEGER NOT NULL,
    "Href" TEXT NOT NULL,
    "SpotifyId" TEXT NOT NULL,
    "IsExternallyHosted" INTEGER NOT NULL,
    "IsPlayable" INTEGER NOT NULL,
    "Language" TEXT NOT NULL,
    "ReleaseDate" TEXT NOT NULL,
    "ReleaseDatePrecision" TEXT NOT NULL,
    "Type" TEXT NOT NULL,
    "SpotifyUri" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "PodcastId" INTEGER NOT NULL,
    CONSTRAINT "FK_Episodes_Podcasts_PodcastId" FOREIGN KEY ("PodcastId") REFERENCES "Podcasts" ("Id") ON DELETE CASCADE
);
CREATE INDEX "IX_Episodes_PodcastId" ON "Episodes" ("PodcastId");
CREATE TABLE IF NOT EXISTS "Podcasts" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Podcasts" PRIMARY KEY AUTOINCREMENT,
    "ShowUri" TEXT NOT NULL,
    "ChartRankMove" TEXT NOT NULL,
    "ShowImageUrl" TEXT NOT NULL,
    "ShowName" TEXT NOT NULL,
    "ShowPublisher" TEXT NOT NULL,
    "ShowDescription" TEXT NOT NULL,
    "Genre" TEXT NOT NULL,
    "IsExplicit" INTEGER NOT NULL,
    "Market" TEXT NOT NULL
);
CREATE UNIQUE INDEX "IX_Podcasts_ShowUri" ON "Podcasts" ("ShowUri");
CREATE TABLE IF NOT EXISTS "RankedPodcasts" (
    "RankingId" INTEGER NOT NULL,
    "PodcastId" INTEGER NOT NULL,
    "Rank" INTEGER NOT NULL,
    CONSTRAINT "PK_RankedPodcasts" PRIMARY KEY ("RankingId"  "PodcastId"),
    CONSTRAINT "FK_RankedPodcasts_Podcasts_PodcastId" FOREIGN KEY ("PodcastId") REFERENCES "Podcasts" ("Id") ON DELETE CASCADE,
    CONSTRAINT "FK_RankedPodcasts_Rankings_RankingId" FOREIGN KEY ("RankingId") REFERENCES "Rankings" ("Id") ON DELETE CASCADE
);
CREATE INDEX "IX_RankedPodcasts_PodcastId" ON "RankedPodcasts" ("PodcastId");
CREATE TABLE IF NOT EXISTS "Rankings" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Rankings" PRIMARY KEY AUTOINCREMENT,
    "Genre" TEXT NOT NULL,
    "Country" TEXT NOT NULL,
    "PodcastDataSetId" INTEGER NULL,
    CONSTRAINT "FK_Rankings_DataSets_PodcastDataSetId" FOREIGN KEY ("PodcastDataSetId") REFERENCES "DataSets" ("Id")
);
CREATE INDEX "IX_Rankings_PodcastDataSetId" ON "Rankings" ("PodcastDataSetId");
'''

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
            sns.barplot(data=data, x='Genre', y='AvgRank', palette=self._palette, ax=ax)
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
        SELECT subquery.Genre, subquery.Country, COALESCE(AvgRank, 200) AS AvgRank
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
            reordered_cluster_grid = sns.clustermap(data=reordered_data, cmap=self._palette + '_r', annot=False, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws)
            reordered_cluster_grid.ax_heatmap.set_xlabel('Country')
            reordered_cluster_grid.ax_heatmap.set_ylabel('Genre')
            reordered_cluster_grid.ax_heatmap.set_title('Average Rank of Podcasts by Genre and Region')

            # Hide the row and column dendrograms
            reordered_cluster_grid.ax_row_dendrogram.set_visible(False)
            reordered_cluster_grid.ax_col_dendrogram.set_visible(False)

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
            reordered_cluster_grid = sns.clustermap(data=reordered_data, cmap=self._palette, annot=True, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws)
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
        SELECT subquery.Genre, subquery.Country, COALESCE(AvgRank, 200) AS AvgRank
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

        # remove 'Unknown' genre from the data
        genre_vs_rank_data = genre_vs_rank_data[genre_vs_rank_data['Genre'] != 'Unknown']

        # merge the two dataframes on Genre and Country
        data = pd.merge(genre_vs_rank_data, genre_vs_presence_data, on=['Genre', 'Country'])

        # clean up the data (0 NumPodcasts -> 1 NumPodcasts)
        data['NumPodcasts'] = data['NumPodcasts'].apply(lambda x: 1 if x == 0 else x)

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
            reordered_cluster_grid = sns.clustermap(data=reordered_data, cmap=self._palette + '_r', annot=False, vmin=abs_min, vmax=abs_max, cbar_kws=cbar_kws, norm=colors.LogNorm())
            reordered_cluster_grid.ax_heatmap.set_xlabel('Country')
            reordered_cluster_grid.ax_heatmap.set_ylabel('Genre')
            reordered_cluster_grid.ax_heatmap.set_title('Popularity of Podcast Genres in Top 200 by Region')

            # Hide the row and column dendrograms
            reordered_cluster_grid.ax_row_dendrogram.set_visible(False)
            reordered_cluster_grid.ax_col_dendrogram.set_visible(False)

            return reordered_cluster_grid.fig

        return AnalyzerResult(data, render)