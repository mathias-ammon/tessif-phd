import os

from tessif.frused.paths import doc_dir

import pandas as pd
import plotly.express as px

PARENT = "CompCnE"

FOLDERS = [
    # "commitment_results",
    "expansion_results",
    # "modified_expansion_results",
]

# FOLDERS = ["trivia_results", ]

FILE = "Capacity.csv"

SOFTWARES = [
    # 'cllp',
    # 'fine',
    'omf',
    # 'ppsa',
]
NOT_NODES = [
    "Biogas Line",
    "Gas Line",
    "Hard Coal Supply Line",
    "Heatline",
    "Lignite Supply Line",
    "Powerline",
]

PLOTLY = False
MATPLOTLIB = True

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

# cp = os.path.join(parent_folder, FOLDER)

for folder in FOLDERS:
    capacities_path = os.path.join(parent_folder, folder, FILE)

    df = pd.read_csv(capacities_path, index_col=0)

    # only keep nodes in NOT_NODES
    keepers = [node for node in df.index if node not in NOT_NODES]
    df = df.loc[keepers]

    # rename df cols and rows for increased verbosity
    df.columns.name = "Softwares"
    df.index.name = "Nodes"

    print(df)

    # original df holds "variable" strings so data needs to be parsed to numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    # store the df as csv for reference
    write_path = os.path.join(
        parent_folder, folder, "Installed_Capacities.csv")
    df.to_csv(write_path)

    folder_title = " ".join(
        [part.capitalize() for part in folder.split("_")])

    if PLOTLY:
        figure = px.bar(
            df,
            barmode="group",
            text_auto=True,
            title="Installed Capacities in MWh " + folder_title,
            template="simple_white",
        )
        figure.show()

    if MATPLOTLIB:
        ax = df.plot(
            kind="bar",
            title="Installed Capacities " + folder_title,
            xlabel="Nodes",
            ylabel="Installed Capacities in MWh",
            rot=45,
        )
        ax.grid(axis='y')
        figure = ax.figure
        figure.show()
