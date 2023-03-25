import os

import pandas as pd

from tessif.analyze import ComparativeResultier
from tessif.identify import (
    TimevaryingIdentificier,
    StaticIdentificier,
    drop_all_zero_rows,
    drop_all_zero_columns,
)
from tessif.frused.paths import doc_dir
from tessif.visualize import component_loads
import tessif.visualize.dcgrph as dcv

FOLDER = "losslc_results"

TITLE = "LossLC - "

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
    "LossLC",
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

# file_location = os.path.join(PARENT, FOLDER, "all_socs.csv")
# all_socs = pd.read_csv(file_location, index_col=0, header=[0, 1])

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

# read in the stored all_loads results
static_all_results = {}
for rtype in [
        "all_capacities",
        "all_original_capacities",
        "all_net_energy_flows",
        "all_costs_incurred",
        "all_emissions_caused",
]:
    file_location = os.path.join(PARENT, FOLDER, f"{rtype}.csv",)

    if rtype in ["all_net_energy_flows", "all_emissions_caused"]:
        static_all_results[rtype] = pd.read_csv(
            file_location, index_col=[0, 1], header=0)
    else:
        static_all_results[rtype] = pd.read_csv(
            file_location, index_col=0, header=0)

cap_sidf = StaticIdentificier(
    data=static_all_results["all_capacities"],
    reference="omf",
)

# --------------------- Summed Loads -------------------#
all_net_flows = static_all_results["all_net_energy_flows"]
all_net_flows = all_net_flows.fillna(0.)
all_net_flows = drop_all_zero_rows(all_net_flows)
all_net_flows = all_net_flows.round().astype(int)
title = TITLE + " Summed Loads"
location = os.path.join(PARENT, FOLDER, "plotted_net_energy_flows.csv",)
all_net_flows.to_csv(location)

ax = all_net_flows.plot(kind="barh", title=title, xlabel="Energy Flow in MWh")
ax.figure.show()

rel_net_flows = all_net_flows.div(all_net_flows["omf"], axis="index")
rel_net_flows = rel_net_flows.round(2)
greater_than_11 = rel_net_flows[rel_net_flows > 1.1].dropna(
    axis="index", how="all").index
lower_than_09 = rel_net_flows[rel_net_flows < 0.9].dropna(
    axis="index", how="all").index
idx = list(greater_than_11) + list(lower_than_09)

rel_net_flows = rel_net_flows.loc[idx]

location = os.path.join(PARENT, FOLDER, "plotted_rel_energy_flows.csv",)
rel_net_flows.to_csv(location)

title = TITLE + " Summed Loads Relative to Oemof (omf)"
ax = rel_net_flows.plot(kind="barh", title=title,
                        xlabel="Relative Energy Flow")
ax.figure.show()


# ------------------Installed Capacities -------------------#
all_installed_capacities = static_all_results["all_capacities"]
all_installed_capacities = all_installed_capacities.fillna(0.)
all_installed_capacities = drop_all_zero_rows(all_installed_capacities)
all_installed_capacities = all_installed_capacities.round().astype(int)
title = TITLE + "Installed Capacities"
location = os.path.join(PARENT, FOLDER, "plotted_installed_capacities.csv",)
all_installed_capacities.to_csv(location)

ax = all_installed_capacities.plot(kind="barh", title=title,
                                   xlabel="Installed Capacity in MWh")
ax.figure.show()


# --------------------- Emissions Caused -------------------#
all_emissions_caused = static_all_results["all_emissions_caused"]
all_emissions_caused = all_emissions_caused.fillna(0.)
all_emissions_caused = drop_all_zero_rows(all_emissions_caused)
all_emissions_caused = all_emissions_caused.round().astype(int)
title = TITLE + "Emissions Caused"
location = os.path.join(PARENT, FOLDER, "plotted_emissions_caused.csv",)
all_emissions_caused.to_csv(location)

ax = all_emissions_caused.plot(kind="barh", title=title,
                               xlabel="Emissions Caused in Tons CO2")
ax.figure.show()

rel_emissions_caused = all_emissions_caused.div(
    all_emissions_caused["omf"], axis="index")
# ------------------States of Charge -------------------#
# title = TITLE + "States of Charge"
# ax = all_socs.plot(
#     kind="line", ylabel="State of Charge in MWh", title=title)
# ax.figure.show()

# location = os.path.join(PARENT, FOLDER, "plotted_socs.csv",)
# all_socs.to_csv(location)


# for flow, flow_results in idf.high_interest_results.items():
#     axes = component_loads.step(flow_results, title=f"{flow[0]} -> {flow[1]}")
#     axes.figure.show()  # commented out for doctesting
