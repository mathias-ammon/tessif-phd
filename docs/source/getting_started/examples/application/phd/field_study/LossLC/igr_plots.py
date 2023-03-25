import pandas as pd


from pathlib import Path

from tessif.frused.paths import doc_dir
from tessif.visualize import igr

mpl_config = {
    "title": "Integrated Global Results Relative to 'Oemof'",
    "ylabel": "",
    "xlabel": "Result Values",
    "rot": 0,
}

for result in ["results", ]:
    igr_results_csv_path = (
        Path(doc_dir)
        / "source"
        / "getting_started"
        / "examples"
        / "application"
        / "phd"
        / "model_scenario_combinations"
        / "LossLC"
        / result
        / "IGR.csv"
    )

    result_df = pd.read_csv(igr_results_csv_path, index_col=0)

    # make results relative to oemof
    result_df = result_df.div(result_df['omf'], axis='index')
    # mpl_config["ylim"] = [
    #     math.floor(10*result_df.min().min())/10,
    #     math.ceil(10*result_df.max().max())/10,
    # ]

    handle = igr.plot(
        igr_df=result_df,
        plt_config=mpl_config,
        ptype="bar",
    )

    for category in ["costs", "non_costs"]:
        figure_storage_path = igr_results_csv_path.parents[0] / "_".join(
            [category, "IGR.png"])

        handle[category].savefig(figure_storage_path)

    # handle["costs"].show()
    # handle["non_costs"].show()


plexp_config = {
    "title": "Integrated Global Results Relative to 'Oemof (omf)'",
    "barmode": "group",
    "text_auto": True,
}


handle = igr.plot(
    igr_df=result_df,
    plt_config=plexp_config,
    ptype="bar",
    draw_util="plexp",
)
handle["costs"].show()
handle["non_costs"].show()
