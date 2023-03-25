from tessif.frused.paths import doc_dir  # nopep8
import os  # nopep8
import pandas as pd  # nopep8


FOLDER = "results"
# SOFTWARES = ('cllp', 'fine', 'ppsa', 'omf',)
SOFTWARES = ('cllp', 'fine', 'ppsa', 'omf',)

# locate the storage directory
current_path = os.path.join(
    doc_dir, "source", "getting_started", "examples", "application",
    "phd", "model_scenario_combinations", "LossLC", FOLDER
)

memory_results = {}
for software in SOFTWARES:
    csv_path = os.path.join(current_path, "_".join(
        [software, "memory_results.csv"]))
    memory_results[software] = pd.read_csv(
        csv_path, index_col=0).to_dict()[software]

memory_df = pd.DataFrame(memory_results)
memory_df.index.name = "Memory [MB]"
csv_path = os.path.join(current_path, "memory_results.csv")
plot_path = os.path.join(current_path, "memory_results.png")
memory_df.to_csv(csv_path)
memory_df.plot(kind="bar", rot=0, figsize=(10, 5)).figure.savefig(plot_path)

timings_results = {}
for software in SOFTWARES:
    csv_path = os.path.join(current_path, "_".join(
        [software, "timings_results.csv"]))
    timings_results[software] = pd.read_csv(
        csv_path, index_col=0).to_dict()[software]

timings_df = pd.DataFrame(timings_results)
timings_df.index.name = "Time [s]"
csv_path = os.path.join(current_path, "timings_results.csv")
plot_path = os.path.join(current_path, "timings_results.png")
timings_df.to_csv(csv_path)
timings_df.plot(kind="bar", rot=0, figsize=(10, 5)).figure.savefig(plot_path)
