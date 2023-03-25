import matplotlib.pyplot as plt

import tessif.visualize.nxgrph as nxv
import tessif.examples.data.tsf.py_hard as tsf_py

tsf_es = tsf_py.create_component_es()
grph = tsf_es.to_nxgrph()
drawing_data = nxv.draw_graph(
    grph,
    node_color={
        'Hard Coal Supply': '#666666',
        'Hard Coal Supply Line': '#666666',
        'Hard Coal PP': '#666666',
        'Hard Coal CHP': '#666666',
        'Solar Panel': '#FF7700',
        'Heat Storage': '#cc0033',
        'Heat Demand': 'Red',
        'Heat Plant': '#cc0033',
        'Heatline': 'Red',
        'Power To Heat': '#cc0033',
        'Biogas CHP': '#006600',
        'Biogas Line': '#006600',
        'Biogas Supply': '#006600',
        'Onshore Wind Turbine': '#99ccff',
        'Offshore Wind Turbine': '#00ccff',
        'Gas Station': '#336666',
        'Gas Line': '#336666',
        'Combined Cycle PP': '#336666',
        'El Demand': '#ffe34d',
        'Battery': '#ffe34d',
        'Powerline': '#ffcc00',
        'Lignite Supply': '#993300',
        'Lignite Supply Line': '#993300',
        'Lignite Power Plant': '#993300',
    },
    node_size={
        'Powerline': 5000,
        'Heatline': 5000
    },
    title='Component Based Example Energy System Graph',
)

plt.show()
