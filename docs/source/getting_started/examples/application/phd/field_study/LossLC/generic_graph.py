import matplotlib.pyplot as plt

import tessif.visualize.dcgrph as dcv
import tessif.examples.data.tsf.py_hard as tsf_py


tsf_es = tsf_py.create_losslc_es()
# grph = tsf_es.to_nxgrph()
app = dcv.draw_generic_graph(
    energy_system=tsf_es,
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
        'High Voltage Transfer Grid': 'yellow',
        'Low Voltage Transfer Grid': 'yellow',
    },
    node_size={
        'High Voltage Transfer Grid': 150,
        'Low Voltage Transfer Grid': 150,
        'District Heating': 150
    },
    title='Lossless Power Grid Example Energy System Graph',
)

app.run_server(debug=False)
