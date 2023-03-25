import os

from tessif import parse
import tessif.visualize.dcgrph as dcv
from tessif.frused.paths import doc_dir

creation_module_path = os.path.join(
    doc_dir,
    "source",
    "getting_started",
    "examples",
    "application",
    "phd",
    "model_scenario_combinations",
    "TransCnE",
    "creation.py",
)

creation_module = parse.python_file(creation_module_path)
transcne_es = creation_module.create_transcne_es()

app = dcv.draw_generic_graph(
    energy_system=transcne_es,
    color_group={
        'Coal Supply': '#666666',
        'Coal Supply Line': '#666666',
        'HKW': '#666666',
        'HKW2': '#666666',
        'Solar Thermal': '#b30000',
        'Heat Storage': '#cc0033',
        'District Heating': 'Red',
        'District Heating Demand': 'Red',
        'Power to Heat': '#b30000',
        'Biogas plant': '#006600',
        'Biogas': '#006600',
        'BHKW': '#006600',
        'Onshore Wind Power': '#99ccff',
        'Offshore Wind Power': '#00ccff',
        'Gas Station': '#336666',
        'Gaspipeline': '#336666',
        'GuD': '#336666',
        'Solar Panel': '#ffe34d',
        'Commercial Demand': '#ffe34d',
        'Household Demand': '#ffe34d',
        'Industrial Demand': '#ffe34d',
        'Car charging Station': '#669999',

        'Low Voltage Grid': '#ffcc00',
        'Medium Voltage Grid': '#ffcc00',
        'High Voltage Grid': '#ffcc00',

        'Low Medium Transfer': '#ff9900',
        'Medium Low Transfer': '#ff9900',

        'High Medium Transfer': '#ff9900',
        'Medium High Transfer': '#ff9900',

        "Excess Sink HV": "yellow",
        "Excess Sink MV": "yellow",
        "Excess Sink LV": "yellow",

        "Deficit Source HV": "yellow",
        "Deficit Source MV": "yellow",
        "Deficit Source LV": "yellow",

    },
    node_size={
        'High Voltage Grid': 150,
        'Medium Voltage Grid': 150,
        'Low Voltage Grid': 150,
        'District Heating': 150
    },
    title='Lossless Power Grid Example Energy System Graph',
)
app.run_server(debug=False)
