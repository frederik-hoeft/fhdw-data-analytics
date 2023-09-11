from typing import Callable, List, Tuple, cast
from matplotlib.dates import YearLocator
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.ticker import MultipleLocator
import numpy as np
from pandas import DataFrame
from sqlalchemy import Engine, create_engine
from analyzers.internals.analyzer_result import AnalyzerResult
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.internals.analyzer_result import AnalyzerResultModel
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns

class DurationGenreClassifierModel(AnalyzerResultModel):
    def __init__(self, analyzer: PodcastAnalyzer, data_frame: DataFrame) -> None:
        super().__init__(data_frame, analyzer._theme, analyzer._palette, lambda result: cast(DurationGenreClassifierModel, result).__render())
        self._set_model_visualizations([])

    # return a formatted time string from a number of milliseconds
    def __format_time(self, millis: float, _):
        formatted_time = pd.to_datetime(millis, unit='ms').strftime('%H:%M:%S')
        return formatted_time

    def __render(self) -> Figure:
        data: DataFrame = self.get_data_frame()

        # Set the style of seaborn
        sns.set_theme(style=self._theme)

        fig, ax = plt.subplots()
        # Create a scatter plot
        sns.scatterplot(
            x="WeightedAvgDurationMs",  # X-axis: Average Duration of Episodes
            y="AvgEpisodes",  # Y-axis: Average Number of Episodes
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
            y = row['AvgEpisodes']
            # check if there is another label with similar coordinates (within 18,750 ms * label size and 10 episodes)
            # if so, move the label up or down a bit. Which direction depends on whether the label is above or below the other label
            for j, other_row in data.iterrows():
                if i != j and abs(other_row['WeightedAvgDurationMs'] - x) < 18750 * max(len(label), len(other_row['Genre'])) and abs(other_row['AvgEpisodes'] - y) < 10:
                    if y > other_row['AvgEpisodes']:
                        y += 6
                    else:
                        y -= 6
                    break
            ax.text(x + 40000, y, label, fontsize=8, va='center')

        ax.set_xlabel('Average Duration of Episodes')
        ax.set_ylabel('Average Number of Episodes per Podcast')
        ax.set_title('Average Duration and Number of Episodes by Genre')
        ax.xaxis.set_major_locator(MultipleLocator(600000))
        ax.xaxis.set_major_formatter(self.__format_time)
        legend: Legend | None = ax.get_legend()
        if legend is not None:
            legend.remove()
        fig.tight_layout()
        return fig
    
    @staticmethod
    def initialize_from_database(connection_string: str) -> 'DurationGenreClassifierModel':
        engine: Engine = create_engine(connection_string)
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
        ''', engine)
        self = DurationGenreClassifierModel(DurationGenreClassifierModel.__dummy_analyzer(connection_string), data)
        return self
    
    def calculate_confidence(self, closest_distance: float, second_closest_distance: float, temperature: float = 1.0):
        """
        Calculate confidence score based on distances to known point in latent space.
        
        Args:
            closest_distance (float): The distance to the closest known point.
            second_closest_distance (float): The distance to the second closest known point.
            temperature (float): A parameter that controls the spread of the confidence scores.
            
        Returns:
            confidence (float): The confidence score between 0 (least confident) and 1 (most confident).
        """
        
        # Calculate unnormalized confidence scores
        unnormalized_confidence = np.exp(-closest_distance / temperature) - np.exp(-second_closest_distance / temperature)
        
        # Normalize the confidence score between 0 and 1
        confidence = 1 / (1 + unnormalized_confidence)
        
        return confidence
    
    def classify(self, duration_ms: float, episodes: int) -> Tuple[str, float]:
        data = self.get_data_frame().copy()

        # normalize the data by dividing by the maximum value in each column
        max_duration = data['WeightedAvgDurationMs'].max()
        max_episodes = data['AvgEpisodes'].max()

        data['WeightedAvgDurationMs'] = data['WeightedAvgDurationMs'] / max_duration
        data['AvgEpisodes'] = data['AvgEpisodes'] / max_episodes

        unknown_podcast = {
            'WeightedAvgDurationMs': duration_ms / max_duration,
            'AvgEpisodes': episodes / max_episodes
        }

        distances = np.sqrt((data['WeightedAvgDurationMs'] - unknown_podcast['WeightedAvgDurationMs']) ** 2 + (data['AvgEpisodes'] - unknown_podcast['AvgEpisodes']) ** 2)
        closest_genre: str = cast(str, data.loc[distances.idxmin(), 'Genre'])
        
        # distance to closest genre
        closest_distance = distances.min()
        # distance to second closest genre (by removing the closest genre from the distances array)
        second_closest_distance = np.delete(distances, distances.idxmin()).min()
        
        confidence = self.calculate_confidence(closest_distance, second_closest_distance)

        return closest_genre, confidence


    class __dummy_analyzer(PodcastAnalyzer):
        def __init__(self, connection_string: str) -> None:
            super().__init__(connection_string, '', '')