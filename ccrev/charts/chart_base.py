from __future__ import annotations

from abc import abstractmethod
from numbers import Number
from typing import List, Union, Iterable, Type

from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from ccrev.rules import Signal


class Plot:
    """
    wrapper and interface for matplotlib canvas to
    include in reports
    """
    FIG_SIZE = (FIG_WIDTH, FIG_HEIGHT) = 6, 3  # in inches

    PLOT_COLS = PLOT_ROWS = PLOT_POS = 1
    _SUBPLOT_GRID = int(str(PLOT_ROWS) + str(PLOT_COLS) + str(PLOT_POS))

    def __init__(self, name=None):
        self.name = name
        self.fig = Figure(Plot.FIG_SIZE)
        self.canvas = FigureCanvas(self.fig)
        self.axes: Axes = self.fig.add_subplot(Plot._SUBPLOT_GRID)

    def add_line(self, data: Union[List[Number], List[List[Number], List[Number]]], **kwargs) -> None:
        """
        add a line to the plot
        """

        def _get_list_of_data_indexes(data: List[Number]) -> List[Number]:
            return list(index for index, _ in enumerate(data, 1))

        new_line = Line2D(
            xdata=_get_list_of_data_indexes(data),
            ydata=data,
            **kwargs
        )
        self.axes.add_line(new_line)

    def resize_plot_axes(self, x_min, x_max, y_min, y_max):
        self.axes.set_xlim(x_min, x_max)
        self.axes.set_ylim(y_min, y_max)

    def save_img(self, file_path: str):
        if file_path.endswith('jpeg'):
            self.canvas.print_jpeg(file_path)
        else:
            self.canvas.print_jpeg(f'{file_path}.jpeg')

    def show_signals(self, signals: List[int], monitored_values: List[float]):
        x_data = list(index if signal > 0 else 0 for index, signal in enumerate(signals, 1))
        y_data = list(val if idx > 0 else None for val, idx in zip(monitored_values, x_data))
        while True:
            try:
                x_data.remove(0)
                y_data.remove(None)
            except ValueError:
                break

        new_line = Line2D(
            xdata=x_data,
            ydata=y_data,
            color='r',
            marker='o',
            markersize=2.2
        )
        new_line.set_linestyle('None')
        self.axes.add_line(new_line)


class ControlChart:
    def __init__(self):
        self.title = None
        self.monitored_values = None
        self._signals = None
        self.center = None
        self._plot_factory = None

    @staticmethod
    def add_stats_data(chart, stats_data):
        for stats_parameter, value in stats_data.items():
            try:
                if chart.stats_parameter:
                    chart.stats_parameter = value
            except AttributeError:
                pass

    @abstractmethod
    def save_plot_as_jpeg(self, file_path: str):
        raise NotImplementedError

class IChart(ControlChart):
    def __init__(self, monitored_data, data_index=None, stats_data=None, title=None):
        super().__init__()
        self.title = title
        self.monitored_values: List[float] = data
        self.standard_deviation: float = None
        super().add_stats_data(self, stats_data)

        self._signals: List[int] = None

        self._center: List[float] = None
        self._plot_factory: Type[Plot] = Plot

    # @property
    # def average(self):
    #     if len(set(self.center)) is 1:
    #         return self.center[0]
    #     else:
    #         raise NotImplementedError('Average for IChart with a non-constant center is undefined')

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value):
        if isinstance(value, (float, int)):
            self._center = [value for _ in range(len(self.monitored_values))]
        elif isinstance(value, Iterable):
            self._center = value
        else:
            raise ValueError('Center must be an iterable, int, or float.')

    @property
    def upper_action_limit(self):
        return [val + 3 * self.standard_deviation for val in self.center]

    @property
    def lower_action_limit(self):
        return [val - 3 * self.standard_deviation for val in self.center]

    @property
    def upper_warning_limit(self):
        return [val + 2 * self.standard_deviation for val in self.center]

    @property
    def lower_warning_limit(self):
        return [val - 2 * self.standard_deviation for val in self.center]

    @property
    def plus_one_standard_deviation(self):
        return [val + self.standard_deviation for val in self.center]

    @property
    def minus_one_standard_deviation(self):
        return [val - self.standard_deviation for val in self.center]

    @property
    def signals(self):
        return self._signals

    @signals.setter
    def signals(self, val):
        try:
            self._signals = []
            for item in val:
                if isinstance(item, int):
                    self._signals.append(item)
                elif isinstance(item, Signal):
                    self._signals.append(item.rule_number)
                else:
                    raise ValueError('IChart.signals can only be set to instances of List[int] and '
                                     'List[Signal]')
        except TypeError:
            self._signals = []
            raise ValueError('IChart.signals can only be set to instances of List[int] and '
                             'List[Signal]')

    @property
    def plot(self, show_signals=True):
        plot = self._plot_factory()
        plot.add_line(self.monitored_values, color='b')
        plot.add_line(self.center, color='k')
        plot.add_line(self.upper_action_limit, color='r')
        plot.add_line(self.lower_action_limit, color='r')
        plot.add_line(self.upper_warning_limit, color='#FF8C00')  # orange
        plot.add_line(self.lower_warning_limit, color='#FF8C00')
        plot.add_line(self.plus_one_standard_deviation, color='g')
        plot.add_line(self.minus_one_standard_deviation, color='g')
        if show_signals:
            plot.show_signals(self.signals, self.monitored_values)
        plot.resize_plot_axes(
            x_min=0,
            x_max=len(self.monitored_values),
            y_min=self.center[0] - 3.5 * self.standard_deviation,
            y_max=self.center[0] + 3.5 * self.standard_deviation
        )
        return plot

    def save_plot_as_jpeg(self, file_path: str):
        self.plot.save_img(file_path)
        return file_path


