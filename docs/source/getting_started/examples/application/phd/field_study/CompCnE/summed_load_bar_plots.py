import plotly.express as px
import os
from collections import defaultdict

from tessif.frused.paths import doc_dir
import matplotlib.pyplot as plt


import pandas as pd

PARENT = "CompCnE"

FOLDER = "commitment_results"
FOLDER = "expansion_results"
FOLDER = "modified_expansion_results"

# FOLDER = "trivia_results"

NODES = [
    "Powerline",
    "Heatline",
]

# locate the storage directory
parent_folder = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "field_study",
    PARENT,
)

cp = os.path.join(parent_folder, FOLDER)


for node in NODES:
    summed_loads_file = f"Load-{node}.csv"
    summed_loads_path = os.path.join(parent_folder, FOLDER, summed_loads_file)

    df = pd.read_csv(summed_loads_path, index_col=0)
    # drop all zero rows
    df = df.loc[(df != 0).any(axis=1)]
    df.columns.name = "softwares"
    # print(node)
    print(df)

    if not df.empty:
        figure = px.bar(
            df,
            barmode="group",
            text_auto=True,
            title=f"{node} Summed Loads",
            template="simple_white",
        )

        ax = df.plot(
            kind="bar",
            title=f"{node} Summed Loads",
            xlabel="Connecting Nodes",
            ylabel="Summed Loads in MW",
            rot=45,
        )
        ax.grid(axis='y')
        figure = ax.figure
        figure.show()
