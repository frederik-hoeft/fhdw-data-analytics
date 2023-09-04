from typing import Callable, List, Tuple, cast
from matplotlib.dates import YearLocator
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from pandas import DataFrame
from analyzers.internals.analyzer_result import AnalyzerResult
from analyzers.podcast_analyzer import PodcastAnalyzer
from analyzers.internals.analyzer_result import AnalyzerResultModel
import numpy as np
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose, DecomposeResult
from scipy.stats import linregress

class UploadFrequencyModel(AnalyzerResultModel):
    def __init__(self, analyzer: PodcastAnalyzer, data_frame: DataFrame) -> None:
        super().__init__(data_frame, analyzer._theme, analyzer._palette, lambda result: cast(UploadFrequencyModel, result).__render())
        self._set_model_visualizations([
            self.upload_model_relative_frequency_vs_month,
            self.upload_model_seasonal,
            self.upload_model_trend,
            self.upload_model_trend_days_per_upload
        ])

    def __render(self) -> Figure:
        data: DataFrame = self.get_data_frame()
        # Set the style of seaborn
        sns.set_theme(style=self._theme)

        fig, ax = plt.subplots() 
        sns.lineplot(data=data, x='Date', y='RelativeUploads', hue='Year', palette=self._palette + '_r', ax=ax)
        ax.set_title('Relative Uploads per Day (Uploads per Podcast per Day)')
        ax.set_xlabel('Date')
        ax.set_ylabel('Relative Uploads')
        ax.xaxis.set_major_locator(YearLocator(base=1))
        fig.tight_layout()
        return fig
    
    def _group_by_month_and_year(self) -> DataFrame:
        data: DataFrame = self.get_data_frame()
        # create copy of data
        data = data.copy()
        # group by month and year
        data['Month'] = data['Date'].dt.month
        data = data.groupby(['Month', 'Year']).mean()
        return data.sort_values(by=['Year', 'Month'])
    
    def _group_by_month(self) -> DataFrame:
        data: DataFrame = self.get_data_frame()
        # create copy of data
        data = data.copy()
        # group by month
        data['Month'] = data['Date'].dt.month
        data = data.groupby(['Month']).mean()
        return data
    
    def _format_month(self, x: int, pos=None) -> str:
        # idk wtf this is but apparently there are 14 months in a year now
        # who knew.
        # also: months are floating point numbers now
        x = int(x)
        if x >= 1 and x <= 12:
            return pd.to_datetime(str(x), format='%m').strftime('%b')
        else:
            return 'fuck you'
    
    def upload_model_relative_frequency_vs_month(self, _: AnalyzerResult) -> Figure:
        data: DataFrame = self._group_by_month_and_year()

        sns.set_theme(style=self._theme)
        fig, ax = plt.subplots()

        sns.lineplot(data=data, x='Month', y='RelativeUploads', hue='Year', palette=self._palette + '_r', ax=ax)
        ax.set_title('Relative Uploads per Day (Uploads per Podcast per Day)')
        ax.set_xlabel('Month')
        ax.set_ylabel('Relative Uploads')
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_major_formatter(self._format_month)
        # rotate x-axis labels by 45 degrees
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
        fig.tight_layout()
        return fig
    
    def _to_time_series(self) -> List[int]:
        data: DataFrame = self._group_by_month_and_year()
        # create time series
        time_series: List[int] = []
        for _, row in data.iterrows():
            time_series.append(row['RelativeUploads'])
        return time_series
    
    def _decompose(self) -> DecomposeResult:
        time_series: List[int] = self._to_time_series()
        return seasonal_decompose(time_series, period=12)
    
    def upload_model_seasonal(self, _: AnalyzerResult) -> Figure:
        decomposition: DecomposeResult = self._decompose()
        seasonal: List[float] = decomposition.seasonal[:12]
        sns.set_theme(style=self._theme)
        fig, ax = plt.subplots()
        sns.lineplot(data=seasonal, ax=ax)
        ax.set_title('Seasonal Upload Components')
        ax.set_xlabel('Month')
        ax.set_ylabel('Relative Uploads')
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_major_formatter(lambda x, _: self._format_month(x + 1))
        # rotate x-axis labels by 45 degrees
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
        fig.tight_layout()
        return fig
    
    # returns the trend of the upload frequency model in uploads per day
    def upload_model_trend(self, _: AnalyzerResult) -> Figure:
        decomposition: DecomposeResult = self._decompose()
        trend: List[float] = decomposition.trend

        min_year: int = int(self.get_data_frame()['Year'].min())

        sns.set_theme(style=self._theme)
        fig, ax = plt.subplots()
        sns.regplot(x=np.arange(len(trend)), y=trend, ax=ax)
        ax.set_title('Season-Adjusted Relative Upload Trend')
        ax.set_xlabel('Year')
        ax.set_ylabel('Uploads per Day')
        ax.xaxis.set_major_locator(MultipleLocator(12))
        ax.xaxis.set_major_formatter(lambda x, _: str(min_year + int(x) // 12))
        #calculate slope and intercept of regression equation
        slope, intercept, r, p, sterr = linregress(
            x=ax.get_lines()[0].get_xdata(),
            y=ax.get_lines()[0].get_ydata())
        # model equation
        equation: str = f'y = {slope}x + {intercept}'
        # add equation to plot
        ax.text(0.05, 0.95, equation, transform=ax.transAxes)
        # hide negative values on the x-axis
        ax.set_xlim(left=0)
        fig.tight_layout()
        return fig
    
    # returns the trend of the upload frequency model in days per upload
    def upload_model_trend_days_per_upload(self, _: AnalyzerResult) -> Figure:
        decomposition: DecomposeResult = self._decompose()
        trend: List[float] = decomposition.trend
        inverse_trend: List[float] = [1 / x for x in trend]

        min_year: int = int(self.get_data_frame()['Year'].min())

        sns.set_theme(style=self._theme)
        fig, ax = plt.subplots()
        # set x axis to include predicted values for the next 18 months
        ax.set_xlim(left=0, right=len(trend) + 18)
        sns.regplot(x=np.arange(len(trend)), y=inverse_trend, truncate=False, ax=ax)
        ax.set_title('Predicted Upload Trend')
        ax.set_xlabel('Year')
        ax.set_ylabel('Days per Upload')
        ax.xaxis.set_major_locator(MultipleLocator(12))
        ax.xaxis.set_major_formatter(lambda x, _: str(min_year + int(x) // 12))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        fig.tight_layout()
        return fig