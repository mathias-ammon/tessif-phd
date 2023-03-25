import os

import pandas as pd

from tessif.analyze import ComparativeResultier
from tessif.identify import (
    TimevaryingIdentificier,
    StaticIdentificier,
)
from tessif.frused.paths import doc_dir
from tessif.visualize import component_loads
import tessif.visualize.dcgrph as dcv
from tessif.visualize.component_loads import step

# FOLDER = "commitment_results"
# FOLDER = "expansion_results"
FOLDER = "modified_expansion_results"

# FOLDER = "trivia_results"
# FOLDER = "avs_results"

# define the softwares to be used
SOFTWARES = ['cllp', 'fine', 'omf', 'ppsa', ]
# use this in case you are just testing out the water
# SOFTWARES = ['omf', 'ppsa', ]

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

# read in the stored all_loads results
all_loads = {}
for software in SOFTWARES:

    file_location = os.path.join(
        PARENT,
        FOLDER,
        f"{software}_all_loads.csv",
    )
    all_loads[software] = pd.read_csv(
        file_location, index_col=0, header=[0, 1])

file_location = os.path.join(PARENT, FOLDER, "all_socs.csv")
all_socs = pd.read_csv(file_location, index_col=0, header=[0, 1])


# create the Identificier using the comparative results:

idf = TimevaryingIdentificier(
    data=all_loads,
    error_value="nmae",
    error_value_threshold=0.1,
    correlation="pearson",
    correlation_threshold=0.7,
    # igr from above show oemof~calliope~fine, hence reference=omf
    reference="omf",
)

print(idf.high)
# print(idf.medium)

file_location = os.path.join(PARENT, FOLDER, "load_interest.csv")
interest = idf.clustered_interest
interest.to_csv(file_location, na_rep="None")

file_location = os.path.join(PARENT, FOLDER, "load_correlation.csv")
corrs = idf.corrs.round(2)
corrs.to_csv(file_location, na_rep="None")

file_location = os.path.join(PARENT, FOLDER, "load_errors.csv")
errors = idf.error_values.round(2)
errors.to_csv(file_location, na_rep="None")

if FOLDER == "modified_expansion_results":

    dtf = idf.high_interest_averaged_results[
        ("Powerline", "Battery")]
    title = "Modified CompE - Battery Charging Flows Significantly Differing from oemof"

    # reorder columns to plot non deviating above pypsa
    dtf = dtf[['ppsa', 'cllp', 'fine', 'omf', ]]
    averaged_high_interest_results = dtf
    file_location = os.path.join(
        PARENT, FOLDER, "averaged_high_interest_results.csv")
    averaged_high_interest_results.to_csv(file_location, na_rep="None")

    ax = averaged_high_interest_results.plot(
        kind="line",
        ylabel="Battery Charging Flow in MW",
        title=title,
        # style=[".", ".", ".", "."],
        color=[
            "#D62728",  # red
            "#1F77B4",  # blue
            "#FF7F0E",  # orange
            "#2CA02C",  # green
        ]
    )
    # ax.figure.show()

    indices = [
        dtf.index
        for dtf in idf.high_interest_timeframes[("Powerline", "Battery")]
    ]
    idx_summeries = [(idx[0], idx[-1]) for idx in indices]
    first_three_indices = idx_summeries[:7]
    ser = pd.Series(first_three_indices)
    ser.name = "(Start, End)"
    ser.index.name = "Index Number"

    file_location = os.path.join(PARENT, FOLDER, "first_three_indices.csv")
    ser.to_csv(file_location)


# read in the stored all_loads results
static_all_results = {}
for rtype in [
        "all_capacities",
        "all_original_capacities",
        "all_net_energy_flows",
        "all_costs_incurred",
        "all_emissions_caused",
]:

    file_location = os.path.join(
        PARENT,
        FOLDER,
        f"{rtype}.csv",
    )

    if rtype == "all_net_energy_flows":
        static_all_results[rtype] = pd.read_csv(
            file_location, index_col=[0, 1], header=0)

    else:
        static_all_results[rtype] = pd.read_csv(
            file_location, index_col=0, header=0)

# print(static_all_results["all_net_energy_flows"])
# print(static_all_results["all_capacities"])

sidf = StaticIdentificier(
    data=static_all_results["all_capacities"],
    reference="omf",
)

file_location = os.path.join(PARENT, FOLDER, "capacities_deviations.csv")
rel_devs = sidf.relative_deviations.round(2)
rel_devs.to_csv(file_location, na_rep="None")

file_location = os.path.join(PARENT, FOLDER, "capacities_interest.csv")
interest = sidf.clustered_interest
interest.to_csv(file_location, na_rep="None")

print(rel_devs)
print(interest)

# ax = averaged_high_interest_results.plot(
#     kind="line",
#     ylabel="Battery Charging Flow in MW",
#     title=title,
#     # style=[".", ".", ".", "."],
#     color=[
#         "#D62728",  # red
#         "#1F77B4",  # blue
#         "#FF7F0E",  # orange
#         "#2CA02C",  # green
#     ]
# )
