import os

import numpy as np
import pandas as pd

import tessif.frused.namedtuples as nts
from tessif.frused.paths import example_dir
from tessif.model import components, energy_system


def create_compcne_es(expansion=False, periods=3):
    """
    Create a model of a generic component based energy system using
    :mod:`tessif's model <tessif.model>`.

    Parameters
    ----------
    expansion : bool, default=False
        Boolean which states whether a commitment problem (False)
        or expansion problem (True) is to be solved

    periods : int, default=3
        Number of time steps of the evaluated timeframe
        (one time step is one hour)

    Returns
    -------
    energy_supply_system_model_scenario_combination
        The created CompC combination.
    """
    # Create a simulation time frame
    timeframe = pd.date_range("1/1/2019", periods=periods, freq="H")

    # Initiate the global constraints depending on the scenario
    if expansion is False:
        global_constraints = {
            "name": "Commitment_Scenario",
            "emissions": float("+inf"),
        }
    else:
        global_constraints = {
            "name": "Expansion_Scenario",
            "emissions": 250000,
        }

    # Variables for timeseries of fluctuate wind, solar and demand

    csv_data = pd.read_csv(
        os.path.join(
            example_dir,
            "data",
            "tsf",
            "load_profiles",
            "component_scenario_profiles.csv",
        ),
        index_col=0,
        sep=";",
    )

    # solar:
    pv = csv_data["pv"].values.flatten()[0:periods]
    # scale relative values with the installed pv power
    pv = pv * 1100

    # wind onshore:
    wind_onshore = csv_data["wind_on"].values.flatten()[0:periods]
    # scale relative values with installed onshore power
    wind_onshore = wind_onshore * 1100

    # wind offshore:
    wind_offshore = csv_data["wind_off"].values.flatten()[0:periods]
    # scale relative values with installed offshore power
    wind_offshore = wind_offshore * 150

    # electricity demand:
    el_demand = csv_data["el_demand"].values.flatten()[0:periods]
    max_el = np.max(el_demand)

    # heat demand:
    th_demand = csv_data["th_demand"].values.flatten()[0:periods]
    max_th = np.max(th_demand)

    # Creating the individual energy system components:

    # ---------------- Sources (incl wind and solar) -----------------------

    hard_coal_supply = components.Source(
        name="Hard Coal Supply",
        outputs=("Hard_Coal",),
        sector="Power",
        carrier="Hard_Coal",
        node_type="source",
        accumulated_amounts={
            "Hard_Coal": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"Hard_Coal": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"Hard_Coal": 0},
        flow_emissions={"Hard_Coal": 0},
        flow_gradients={
            "Hard_Coal": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"Hard_Coal": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={"Hard_Coal": False},
        expansion_costs={"Hard_Coal": 0},
        expansion_limits={"Hard_Coal": nts.MinMax(min=0, max=float("+inf"))},
    )

    lignite_supply = components.Source(
        name="Lignite Supply",
        outputs=("lignite",),
        sector="Power",
        carrier="Lignite",
        node_type="source",
        accumulated_amounts={"lignite": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"lignite": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"lignite": 0},
        flow_emissions={"lignite": 0},
        flow_gradients={
            "lignite": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"lignite": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={"lignite": False},
        expansion_costs={"lignite": 0},
        expansion_limits={"lignite": nts.MinMax(min=0, max=float("+inf"))},
    )

    fuel_supply = components.Source(
        name="Gas Station",
        outputs=("fuel",),
        sector="Power",
        carrier="Gas",
        node_type="source",
        accumulated_amounts={"fuel": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"fuel": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"fuel": 0},
        flow_emissions={"fuel": 0},
        flow_gradients={
            "fuel": nts.PositiveNegative(positive=float("+inf"), negative=float("+inf"))
        },
        gradient_costs={"fuel": nts.PositiveNegative(positive=0, negative=0)},
        timeseries=None,
        expandable={"fuel": False},
        expansion_costs={"fuel": 0},
        expansion_limits={"fuel": nts.MinMax(min=0, max=float("+inf"))},
    )

    biogas_supply = components.Source(
        name="Biogas Supply",
        outputs=("biogas",),
        sector="Power",
        carrier="Biogas",
        node_type="source",
        accumulated_amounts={"biogas": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"biogas": nts.MinMax(min=0, max=float("+inf"))},
        flow_costs={"biogas": 0},
        flow_emissions={"biogas": 0},
        flow_gradients={
            "biogas": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"biogas": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={"biogas": False},
        expansion_costs={"biogas": 0},
        expansion_limits={"biogas": nts.MinMax(min=0, max=float("+inf"))},
    )

    solar_panel = components.Source(
        name="Solar Panel",
        outputs=("electricity",),
        sector="Power",
        carrier="electricity",
        node_type="Renewable",
        accumulated_amounts={
            "electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"electricity": nts.MinMax(min=0, max=1100)},
        flow_costs={"electricity": 80},
        flow_emissions={"electricity": 0.05},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"electricity": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={
            "electricity": nts.MinMax(min=np.array(periods * [0]), max=np.array(pv))
        },
        expandable={"electricity": expansion},
        expansion_costs={"electricity": 1000000},
        expansion_limits={"electricity": nts.MinMax(
            min=1100, max=float("+inf"))},
    )

    onshore_wind_turbine = components.Source(
        name="Onshore Wind Turbine",
        outputs=("electricity",),
        sector="Power",
        carrier="electricity",
        node_type="Renewable",
        accumulated_amounts={
            "electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"electricity": nts.MinMax(min=0, max=1100)},
        flow_costs={"electricity": 60},
        flow_emissions={"electricity": 0.02},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"electricity": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={
            "electricity": nts.MinMax(
                min=np.array(periods * [0]), max=np.array(wind_onshore)
            )
        },
        expandable={"electricity": expansion},
        expansion_costs={"electricity": 1750000},
        expansion_limits={"electricity": nts.MinMax(
            min=1100, max=float("+inf"))},
    )

    offshore_wind_turbine = components.Source(
        name="Offshore Wind Turbine",
        outputs=("electricity",),
        sector="Power",
        carrier="electricity",
        node_type="Renewable",
        accumulated_amounts={
            "electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"electricity": nts.MinMax(min=0, max=150)},
        flow_costs={"electricity": 105},
        flow_emissions={"electricity": 0.02},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"electricity": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={
            "electricity": nts.MinMax(
                min=np.array(periods * [0]), max=np.array(wind_offshore)
            )
        },
        expandable={"electricity": expansion},
        expansion_costs={"electricity": 3900000},
        expansion_limits={"electricity": nts.MinMax(
            min=150, max=float("+inf"))},
    )

    # ---------------- Transformer -----------------------

    hard_coal_chp = components.Transformer(
        name="Hard Coal CHP",
        inputs=("Hard_Coal",),
        outputs=(
            "electricity",
            "hot_water",
        ),
        conversions={
            ("Hard_Coal", "electricity"): 0.4,
            ("Hard_Coal", "hot_water"): 0.4,
        },
        sector="Coupled",
        carrier="coupled",
        node_type="transformer",
        flow_rates={
            "Hard_Coal": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=0, max=300),
            "hot_water": nts.MinMax(min=0, max=300),
        },
        flow_costs={"Hard_Coal": 0, "electricity": 80, "hot_water": 6},
        flow_emissions={"Hard_Coal": 0, "electricity": 0.8, "hot_water": 0.06},
        flow_gradients={
            "Hard_Coal": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "Hard_Coal": nts.PositiveNegative(positive=0, negative=0),
            "electricity": nts.PositiveNegative(positive=0, negative=0),
            "hot_water": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={
            "Hard_Coal": False,
            "electricity": expansion,
            "hot_water": expansion,
        },
        expansion_costs={"Hard_Coal": 0,
                         "electricity": 1750000, "hot_water": 131250},
        expansion_limits={
            "Hard_Coal": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=300, max=float("+inf")),
            "hot_water": nts.MinMax(min=300, max=float("+inf")),
        },
    )

    hard_coal_power_plant = components.Transformer(
        name="Hard Coal PP",
        inputs=("Hard_Coal",),
        outputs=("electricity",),
        conversions={("Hard_Coal", "electricity"): 0.43},
        sector="Power",
        carrier="electricity",
        node_type="transformer",
        flow_rates={
            "Hard_Coal": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=0, max=500),
        },
        flow_costs={"Hard_Coal": 0, "electricity": 80},
        flow_emissions={"Hard_Coal": 0, "electricity": 0.8},
        flow_gradients={
            "Hard_Coal": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "Hard_Coal": nts.PositiveNegative(positive=0, negative=0),
            "electricity": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={"Hard_Coal": False, "electricity": expansion},
        expansion_costs={"Hard_Coal": 0, "electricity": 1650000},
        expansion_limits={
            "Hard_Coal": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=500, max=float("+inf")),
        },
    )

    combined_cycle_power_plant = components.Transformer(
        name="Combined Cycle PP",
        inputs=("fuel",),
        outputs=("electricity",),
        conversions={("fuel", "electricity"): 0.6},
        sector="Power",
        carrier="electricity",
        node_type="transformer",
        flow_rates={
            "fuel": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=0, max=600),
        },
        flow_costs={"fuel": 0, "electricity": 90},
        flow_emissions={"fuel": 0, "electricity": 0.35},
        flow_gradients={
            "fuel": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "fuel": nts.PositiveNegative(positive=0, negative=0),
            "electricity": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={"fuel": False, "electricity": expansion},
        expansion_costs={"fuel": 0, "electricity": 950000},
        expansion_limits={
            "fuel": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=600, max=float("+inf")),
        },
    )

    lignite_power_plant = components.Transformer(
        name="Lignite Power Plant",
        inputs=("lignite",),
        outputs=("electricity",),
        conversions={("lignite", "electricity"): 0.4},
        sector="Power",
        carrier="electricity",
        node_type="transformer",
        flow_rates={
            "lignite": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=0, max=500),
        },
        flow_costs={"lignite": 0, "electricity": 65},
        flow_emissions={"lignite": 0, "electricity": 1},
        flow_gradients={
            "lignite": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "lignite": nts.PositiveNegative(positive=0, negative=0),
            "electricity": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={"lignite": False, "electricity": expansion},
        expansion_costs={"lignite": 0, "electricity": 1900000},
        expansion_limits={
            "lignite": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=500, max=float("+inf")),
        },
    )

    biogas_chp = components.Transformer(
        name="Biogas CHP",
        inputs=("biogas",),
        outputs=(
            "electricity",
            "hot_water",
        ),
        conversions={("biogas", "electricity"): 0.4,
                     ("biogas", "hot_water"): 0.5},
        sector="Coupled",
        carrier="coupled",
        node_type="transformer",
        flow_rates={
            "biogas": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=0, max=200),
            "hot_water": nts.MinMax(min=0, max=250),
        },
        flow_costs={"biogas": 0, "electricity": 150, "hot_water": 11.25},
        flow_emissions={"biogas": 0,
                        "electricity": 0.25, "hot_water": 0.01875},
        flow_gradients={
            "biogas": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "biogas": nts.PositiveNegative(positive=0, negative=0),
            "electricity": nts.PositiveNegative(positive=0, negative=0),
            "hot_water": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={
            "biogas": False,
            "electricity": expansion,
            "hot_water": expansion,
        },
        expansion_costs={"biogas": 0,
                         "electricity": 3500000, "hot_water": 262500},
        expansion_limits={
            "biogas": nts.MinMax(min=0, max=float("+inf")),
            "electricity": nts.MinMax(min=200, max=float("+inf")),
            "hot_water": nts.MinMax(min=250, max=float("+inf")),
        },
    )

    heat_plant = components.Transformer(
        name="Heat Plant",
        inputs=("fuel",),
        outputs=("hot_water",),
        conversions={("fuel", "hot_water"): 0.9},
        sector="Power",
        carrier="hot_water",
        node_type="transformer",
        flow_rates={
            "fuel": nts.MinMax(min=0, max=float("+inf")),
            "hot_water": nts.MinMax(min=0, max=450),
        },
        flow_costs={"fuel": 0, "hot_water": 35},
        flow_emissions={"fuel": 0, "hot_water": 0.23},
        flow_gradients={
            "fuel": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "fuel": nts.PositiveNegative(positive=0, negative=0),
            "hot_water": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={"fuel": False, "hot_water": expansion},
        expansion_costs={"fuel": 0, "hot_water": 390000},
        expansion_limits={
            "fuel": nts.MinMax(min=0, max=float("+inf")),
            "hot_water": nts.MinMax(min=450, max=float("+inf")),
        },
    )

    power_to_heat = components.Transformer(
        name="Power To Heat",
        inputs=("electricity",),
        outputs=("hot_water",),
        conversions={("electricity", "hot_water"): 0.99},
        sector="Coupled",
        carrier="coupled",
        node_type="transformer",
        flow_rates={
            "electricity": nts.MinMax(min=0, max=float("+inf")),
            "hot_water": nts.MinMax(min=0, max=100),
        },
        flow_costs={"electricity": 0, "hot_water": 20},
        flow_emissions={"electricity": 0, "hot_water": 0.0007},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            ),
        },
        gradient_costs={
            "electricity": nts.PositiveNegative(positive=0, negative=0),
            "hot_water": nts.PositiveNegative(positive=0, negative=0),
        },
        timeseries=None,
        expandable={"electricity": False, "hot_water": expansion},
        expansion_costs={"electricity": 0, "hot_water": 100000},
        expansion_limits={
            "electricity": nts.MinMax(min=0, max=float("+inf")),
            "hot_water": nts.MinMax(min=100, max=float("+inf")),
        },
    )

    # ---------------- Storages -----------------------

    storage = components.Storage(
        name="Battery",
        input="electricity",
        output="electricity",
        capacity=100,
        initial_soc=0,
        sector="Power",
        carrier="electricity",
        node_type="storage",
        idle_changes=nts.PositiveNegative(positive=0, negative=0.5),
        flow_rates={"electricity": nts.MinMax(min=0, max=33)},
        flow_efficiencies={"electricity": nts.InOut(
            inflow=0.95, outflow=0.95)},
        flow_costs={"electricity": 400},
        flow_emissions={"electricity": 0.06},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"electricity": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={"capacity": expansion,
                    "electricity": expansion},
        fixed_expansion_ratios={"electricity": expansion},
        expansion_costs={"capacity": 1630000, "electricity": 0},
        expansion_limits={
            "capacity": nts.MinMax(min=100, max=float("+inf")),
            "electricity": nts.MinMax(min=33, max=float("+inf")),
        },
    )

    heat_storage = components.Storage(
        name="Heat Storage",
        input="hot_water",
        output="hot_water",
        capacity=50,
        initial_soc=0,
        sector="Heat",
        carrier="hot_water",
        node_type="storage",
        idle_changes=nts.PositiveNegative(positive=0, negative=0.25),
        flow_rates={"hot_water": nts.MinMax(min=0, max=10)},
        flow_efficiencies={"hot_water": nts.InOut(inflow=0.95, outflow=0.95)},
        flow_costs={"hot_water": 20},
        flow_emissions={"hot_water": 0},
        flow_gradients={
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"hot_water": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries=None,
        expandable={"capacity": expansion,
                    "hot_water": expansion},
        fixed_expansion_ratios={"hot_water": expansion},
        expansion_costs={"capacity": 4500, "hot_water": 0},
        expansion_limits={
            "capacity": nts.MinMax(min=50, max=float("+inf")),
            "hot_water": nts.MinMax(min=10, max=float("+inf")),
        },
    )

    # ---------------- Sinks -----------------------

    el_demand = components.Sink(
        name="El Demand",
        inputs=("electricity",),
        sector="Power",
        carrier="electricity",
        node_type="demand",
        accumulated_amounts={
            "electricity": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"electricity": nts.MinMax(min=0, max=max_el)},
        flow_costs={"electricity": 0},
        flow_emissions={"electricity": 0},
        flow_gradients={
            "electricity": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"electricity": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={
            "electricity": nts.MinMax(min=np.array(el_demand), max=np.array(el_demand))
        },
        expandable={"electricity": False},
        expansion_costs={"electricity": 0},
        expansion_limits={"electricity": nts.MinMax(min=0, max=float("+inf"))},
    )

    heat_demand = components.Sink(
        name="Heat Demand",
        inputs=("hot_water",),
        sector="Heat",
        carrier="hot_water",
        node_type="demand",
        accumulated_amounts={
            "hot_water": nts.MinMax(min=0, max=float("+inf"))},
        flow_rates={"hot_water": nts.MinMax(min=0, max=max_th)},
        flow_costs={"hot_water": 0},
        flow_emissions={"hot_water": 0},
        flow_gradients={
            "hot_water": nts.PositiveNegative(
                positive=float("+inf"), negative=float("+inf")
            )
        },
        gradient_costs={"hot_water": nts.PositiveNegative(
            positive=0, negative=0)},
        timeseries={
            "hot_water": nts.MinMax(min=np.array(th_demand), max=np.array(th_demand))
        },
        expandable={"hot_water": False},
        expansion_costs={"hot_water": 0},
        expansion_limits={"hot_water": nts.MinMax(min=0, max=float("+inf"))},
    )

    # ---------------- Busses -----------------------

    fuel_supply_line = components.Bus(
        name="Gas Line",
        inputs=("Gas Station.fuel",),
        outputs=("Combined Cycle PP.fuel", "Heat Plant.fuel"),
        sector="Coupled",
        carrier="Gas",
        node_type="bus",
    )

    biogas_supply_line = components.Bus(
        name="Biogas Line",
        inputs=("Biogas Supply.biogas",),
        outputs=("Biogas CHP.biogas",),
        sector="Coupled",
        carrier="Biogas",
        node_type="bus",
    )

    hard_coal_supply_line = components.Bus(
        name="Hard Coal Supply Line",
        inputs=("Hard Coal Supply.Hard_Coal",),
        outputs=(
            "Hard Coal PP.Hard_Coal",
            "Hard Coal CHP.Hard_Coal",
        ),
        sector="Coupled",
        carrier="Hard_Coal",
        node_type="bus",
    )

    lignite_supply_line = components.Bus(
        name="Lignite Supply Line",
        inputs=("Lignite Supply.lignite",),
        outputs=("Lignite Power Plant.lignite",),
        sector="Power",
        carrier="Lignite",
        node_type="bus",
    )

    electricity_line = components.Bus(
        name="Powerline",
        inputs=(
            "Combined Cycle PP.electricity",
            "Battery.electricity",
            "Lignite Power Plant.electricity",
            "Hard Coal PP.electricity",
            "Hard Coal CHP.electricity",
            "Solar Panel.electricity",
            "Offshore Wind Turbine.electricity",
            "Biogas CHP.electricity",
            "Onshore Wind Turbine.electricity",
        ),
        outputs=(
            "El Demand.electricity",
            "Battery.electricity",
            "Power To Heat.electricity",
        ),
        sector="Power",
        carrier="electricity",
        node_type="bus",
    )

    heat_line = components.Bus(
        name="Heatline",
        inputs=(
            "Heat Plant.hot_water",
            "Hard Coal CHP.hot_water",
            "Biogas CHP.hot_water",
            "Power To Heat.hot_water",
            "Heat Storage.hot_water",
        ),
        outputs=("Heat Demand.hot_water", "Heat Storage.hot_water"),
        sector="Heat",
        carrier="hot_water",
        node_type="bus",
    )

    # Creating the actual energy system:

    explicit_es = energy_system.AbstractEnergySystem(
        uid="Component_es",
        busses=(
            fuel_supply_line,
            electricity_line,
            hard_coal_supply_line,
            lignite_supply_line,
            biogas_supply_line,
            heat_line,
        ),
        sinks=(el_demand, heat_demand),
        sources=(
            fuel_supply,
            solar_panel,
            onshore_wind_turbine,
            hard_coal_supply,
            lignite_supply,
            offshore_wind_turbine,
            biogas_supply,
        ),
        transformers=(
            combined_cycle_power_plant,
            hard_coal_power_plant,
            lignite_power_plant,
            biogas_chp,
            heat_plant,
            power_to_heat,
            hard_coal_chp,
        ),
        storages=(storage, heat_storage),
        timeframe=timeframe,
        global_constraints=global_constraints,
    )

    return explicit_es
