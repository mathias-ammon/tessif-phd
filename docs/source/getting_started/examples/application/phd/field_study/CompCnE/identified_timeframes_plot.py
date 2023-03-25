import os

import matplotlib.pyplot as plt
import pandas as pd

from tessif.frused.paths import doc_dir

# FOLDER = "commitment_results"
# FOLDER = "expansion_results"
FOLDER = "modified_expansion_results"
# FOLDER = "trivia_results"
# FOLDER = "avs_results"

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]


PARENT = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    "CompCnE",
)

dataframes = []
for i in range(4):
    file_location = os.path.join(PARENT, FOLDER, f"ISD2_BatteryCharging{i+1}.csv")
    dtf = pd.read_csv(file_location, index_col=0, header=0, parse_dates=True)
    dtf = dtf.drop(["Calliope", "FINE"], axis="columns")
    dataframes.append(dtf)


colors = [
    "#D62728",  # red
    # "#1F77B4",  # blue
    # "#FF7F0E",  # orange
    "#2CA02C",  # green
]

fig, axes = plt.subplots(2, 2, sharey=True)
axes = [ax for row in axes for ax in row]

for i, (ax, dtf) in enumerate(zip(axes, dataframes)):

    ax.set_title(f"Identified Timeframe - {i+1}")

    # dtf.plot(
    #     kind="bar",
    #     color=colors,
    #     ax=ax,
    # )

    for n, column in enumerate(dtf):
        ax.step(
            # kind="step",
            # x=dtf.index.strftime('%Y/%m/%d H: %H'),
            x=dtf.index.strftime('%m.%d - %H:%M'),
            y=dtf[column],
            c=colors[n],
            label=column,
            # ylabel="Battery Charging Flow in MW",
            # style=[".", ".", ".", "."],
            where="post",

        )

        ax.grid(visible=True, which='major', axis='y')
        ax.grid(visible=True, which='minor', axis='y',
                linestyle="--", linewidth=0.25)

        ax.legend(fontsize=12)
        if i % 2 == 0:
            ax.set_ylabel("Power in MW")

        for label in ax.get_xticklabels():
            label.set_ha("right")
            label.set_rotation(45)
        # # Get the current xtick labels
        # xtick_labels = ax.get_xticklabels()

        # # Set the new xtick labels with rotation
        # ax.set_xticklabels(xtick_labels, rotation=45)


fig.show()
