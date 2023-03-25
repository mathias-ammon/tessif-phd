# interfaces/visualize/demand.py
"""
Load duration curve - Plotting load (in given unit) over cumulated time
(in given unit).

"""
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import collections
import pandas as pd
import itertools
from itertools import cycle
import logging

logger = logging.getLogger(__name__)


def listify(obj):
    return [obj] if isinstance(obj, str) else obj


def nestify(iterable):
    return [iterable] if not all(isinstance(item, collections.Iterable)
                                 for item in iterable) else iterable


def infer(iterable, attr):
    if hasattr(iterable, attr):
        return getattr(iterable, attr)
    else:
        logger.warning(
            "\nCould not infer {} from \n{}\n".format(attr, iterable) +
            "State {} explicitly. ".format(attr) +
            "Or implement a \'{}.{}\' attribute.\n".format(type(iterable), attr))
        return None


def plot(power_loads=[], heat_loads=[], power_labels=[],
         heat_labels=[], power_colors=None, heat_colors=None,
         power_hatches=[], heat_hatches=[], load_unit='MW',
         xlabel='', title='Demand curves',  date_format='%a. %m-%d',
         tick_distance=2, **kwargs):

    if power_loads is not None:
        power_loads = nestify(power_loads)
    if heat_loads is not None:
        heat_loads = nestify(heat_loads)

#    print('power_loads'
    power_loads = list(reversed(power_loads))
    heat_loads = list(reversed(heat_loads))

    # 1.2) Try to infer labels from loads.name attribute:
    # 1.2.1) Power loads:
    if power_loads and not power_labels:
        for load in power_loads:
            power_labels.append(
                infer(load, 'name'))

    # 1.2.3) Heat loads:
    if heat_loads and not heat_labels:
        for load in heat_loads:
            heat_labels.append(
                infer(load, 'name'))

    # 2.) Prepare meta data:
    # 2.1) Make sure explitly stated label is an indexible container:
    if power_labels:
        power_labels = listify(power_labels)
    if heat_labels:
        heat_labels = listify(heat_labels)

    power_labels = list(reversed(power_labels))
    heat_labels = list(reversed(heat_labels))

    # 2.2) Prepare x axis:
    # 2.2.1) Try to infer DateTimeIndex from loads.index:
    for load in itertools.chain(power_loads, heat_loads):
        if isinstance(load, (pd.Series, pd.DataFrame)):
            index = list(infer(load, 'index'))
        else:
            index = list(range(len(load)))

    # 2.2.2) Compute x_ticks:
    # 0...0+tick_distance...x(final_load_entry):
    xticks = range(0, len(index), tick_distance)

    # 2.2.3)
    xticklabels = list(tick.strftime(date_format)
                       if not isinstance(tick, int) else tick
                       for tick in index[0::tick_distance])

    # 3) Set colors:
    if not power_colors:
        power_colors = ['#FCE205', '#FDE64B', '#F9C801', '#F9A602']
    if not heat_colors:
        heat_colors = ['#AA0000', '#D40000', '#FF0000', '#FF2A2A']

    power_color_theme = cycle(power_colors)
    heat_color_theme = cycle(heat_colors)

    # 4) Set hatches:
    if not power_hatches:
        power_hatches = [',', '', '/', '\\', '|',
                         '-', '+', 'x', 'o', 'O', '.', '*']
    if not heat_hatches:
        heat_hatches = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']

    power_hatch_theme = cycle(power_hatches)
    heat_hatch_theme = cycle(heat_hatches)

    # 2.) Create an empty canvas to draw on:
    if power_loads and heat_loads:
        # .1a) Both load serieses are categorized by sector
        if len(power_loads) > 1 and len(heat_loads) > 1:
            f, ax = plt.subplots(3, 1, sharex=False, tight_layout=True)
            # .1) Stacked heat and power plot cumulated:
            sum_heat_loads = list(sum(loads) for loads in zip(*heat_loads))
            ax[0].bar(
                list(range(len(sum_heat_loads))), sum_heat_loads,
                label='Heat', color=next(heat_color_theme),
                width=1.0,  **kwargs)
            sum_power_loads = list(sum(loads) for loads in zip(*power_loads))
            ax[0].bar(
                list(range(len(sum_power_loads))), sum_power_loads,
                color=next(power_color_theme), label='Power', width=1.0,
                bottom=sum_heat_loads if sum_heat_loads else 0, **kwargs)
            ax[0].set_title('Heat & Power')
            # .2) Stacked power plot differentiated by category:
            for pos, load in enumerate(power_loads):
                bottom = list(sum(loads) for loads in zip(*power_loads[:pos]))
                ax[1].bar(
                    list(range(len(load))), load,  label=power_labels[pos],
                    width=1.0, color=next(power_color_theme),
                    hatch=next(power_hatch_theme),
                    bottom=bottom if bottom else 0)
            ax[1].set_title('Power')
            # .3) Stacked heat plot differentiated by category:
            for pos, load in enumerate(heat_loads):
                bottom = list(sum(loads)
                              for loads in zip(*heat_loads[:pos]))
                ax[2].bar(
                    list(range(len(load))), load, label=heat_labels[pos],
                    color=next(heat_color_theme), width=1.0,
                    hatch=next(heat_hatch_theme),
                    bottom=bottom if bottom else 0, **kwargs)
            ax[2].set_title('Heat')

        # .1b) Power loads are categorized by sector
        elif len(power_loads) > 1:
            f, ax = plt.subplots(2, 1, sharex=False, tight_layout=True)

            # .1) Stacked heat and power plot cumulated:
            sum_heat_loads = list(sum(loads) for loads in zip(*heat_loads))
            ax[0].bar(
                list(range(len(sum_heat_loads))), sum_heat_loads,
                label='Heat', color=next(heat_color_theme),
                width=1.0,  **kwargs)
            sum_power_loads = list(sum(loads) for loads in zip(*power_loads))
            ax[0].bar(
                list(range(len(sum_power_loads))), sum_power_loads,
                label='Power', color=next(power_color_theme), width=1.0,
                bottom=sum_heat_loads if sum_heat_loads else 0, **kwargs)
            ax[0].set_title('Heat & Power')

            # .2) Stacked power plot differentiated by category:
            for pos, load in enumerate(power_loads):
                bottom = list(sum(loads) for loads in zip(*power_loads[:pos]))
                ax[1].bar(
                    list(range(len(load))), load,  label=power_labels[pos],
                    width=1.0, color=next(power_color_theme),
                    hatch=next(power_hatch_theme),
                    bottom=bottom if bottom else 0)
            ax[1].set_title('Power')

        # .1c) heat loads are categorized by sector:
        elif len(heat_loads) > 1:
            f, ax = plt.subplots(2, 1, sharex=False, tight_layout=True)
            # .1) Stacked heat and power plot cumulated:
            sum_heat_loads = list(sum(loads) for loads in zip(*heat_loads))
            ax[0].bar(
                list(range(len(sum_heat_loads))), sum_heat_loads,
                label='Heat', color=next(heat_color_theme),
                width=1.0,  **kwargs)
            sum_power_loads = list(sum(loads) for loads in zip(*power_loads))
            ax[0].bar(
                list(range(len(sum_power_loads))), sum_power_loads,
                label='Power', color=next(power_color_theme), width=1.0,
                bottom=sum_heat_loads if sum_heat_loads else 0, **kwargs)
            ax[0].set_title('Heat & Power')
            # .2) Stacked heat plot differentiated by category:
            for pos, load in enumerate(heat_loads):
                bottom = list(sum(loads)
                              for loads in zip(*heat_loads[:pos]))
                ax[1].bar(
                    list(range(len(load))), load, label=heat_labels[pos],
                    color=next(heat_color_theme), width=1.0,
                    hatch=next(heat_hatch_theme),
                    bottom=bottom if bottom else 0, **kwargs)
            ax[1].set_title('Heat')

        # .1d) Both load series are uncategorized
        else:
            f, ax = plt.subplots(1, 1, sharex=False, tight_layout=True)
            # .1) Stacked heat and power plot cumulated:
            sum_heat_loads = list(sum(loads) for loads in zip(*heat_loads))
            ax.bar(
                list(range(len(sum_heat_loads))), sum_heat_loads,
                label='Heat', color=next(heat_color_theme), width=1.0,  **kwargs)
            sum_power_loads = list(sum(loads) for loads in zip(*power_loads))
            ax.bar(
                list(range(len(sum_power_loads))), sum_power_loads,
                label='Power', color=next(power_color_theme), width=1.0,
                bottom=sum_heat_loads if sum_heat_loads else 0, **kwargs)
            ax.set_title('Heat & Power')

    # .2) Only one of the two load series was passed:
    else:
        # .2a) Stacked power plot differentiated by category:
        if power_loads:
            f, ax = plt.subplots(1, 1, sharex=False, tight_layout=True)

            print(power_loads)
            print(power_labels)
            for pos, load in enumerate(power_loads):
                print('Pos: ', pos, 'Load:', load,)
                bottom = list(sum(loads) for loads in zip(*power_loads[:pos]))
                ax.bar(
                    list(range(len(load))), load,
                    label=power_labels[pos] if len(power_loads) > 1 else None,
                    width=1.0, color=next(power_color_theme),
                    hatch=next(power_hatch_theme),
                    bottom=bottom if bottom else 0)
            ax.set_title('Power')

        # .2b) Stacked heat plot differentiated by category:
        if heat_loads:
            f, ax = plt.subplots(1, 1, sharex=False, tight_layout=True)
            for pos, load in enumerate(heat_loads):
                bottom = list(sum(loads)
                              for loads in zip(*heat_loads[:pos]))
                ax.bar(
                    list(range(len(load))), load,
                    label=heat_labels[pos] if len(heat_loads) > 1 else None,
                    color=next(heat_color_theme), width=1.0,
                    bottom=bottom if bottom else 0, **kwargs)
            ax.set_title('Heat')

    # 4.) Format the axis:
    for axis in ax if isinstance(ax, collections.Iterable) else [ax]:
        # 4.1) X-Axis:
        # 4.1.1) Set label:

        axis.set_xlabel('{}'.format(xlabel))
        # 4.1.2) Only allow integers as ticks
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))

        axis.set_xticks(xticks, minor=False)

        axis.set_xticklabels(xticklabels,
                             rotation=0, minor=False)

        # 5.2) Y-Axis:
        # 5.2.1) Set label:
        axis.set_ylabel('{}'.format(load_unit))
        # 5.2.2) Make Y-Axis always start from 0:
        axis.set_ylim(bottom=0)

        # 7.) Draw the legend
        handles, labels = axis.get_legend_handles_labels()
        if labels:
            axis.legend(handles[::-1], labels[::-1])
