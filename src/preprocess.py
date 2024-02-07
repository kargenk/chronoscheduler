from pathlib import Path

import pandas as pd

from generate_mock_data import make_constraints, make_mappings

if __name__ == "__main__":
    DATA_DIR = Path(__file__).parents[1].joinpath("data", "kiu")
    semesters = [1, 2]  # 1: 前期, 2: 後期, 3: 通期
    dtype = {"授業コード": str, "対象コース": str}

    df_lecture = pd.read_csv(
        DATA_DIR.joinpath("lecture_properties.csv"), encoding="utf-8", dtype=dtype
    )
    df_room = pd.read_csv(DATA_DIR.joinpath("rooms.csv"), encoding="utf-8")
    with open(DATA_DIR.joinpath("periods.csv"), encoding="utf-8") as f:
        periods = [t.strip("\n") for t in f.read().split(",")]

    for semester in semesters:
        if semester == 1:
            save_dir = DATA_DIR.joinpath("first")
            idx = df_lecture["開講期"].isin([1, 3])
        elif semester == 2:
            save_dir = DATA_DIR.joinpath("second")
            idx = df_lecture["開講期"].isin([2])
        save_dir.mkdir(parents=True, exist_ok=True)
        codes = df_lecture[idx]["授業コード"].to_list()

        df_lecture[idx].to_csv(
            save_dir.joinpath("lecture_properties.csv"),
            index=False,
            header=True,
            encoding="utf-8",
        )

        # 情報のマッピングと制約定義
        make_mappings(save_dir, df_lecture[idx], codes)
        make_constraints(save_dir, df_lecture[idx], df_room, periods)

    # 連続した授業群だけ先に割り当てするために分けて保存
    for i, name in zip(semesters, ["first", "second"]):
        save_dir = DATA_DIR.joinpath("zeroth_continuous", name)
        save_dir.mkdir(parents=True, exist_ok=True)

        # 該当授業のみを抽出して制約とマッピングを作成
        continuous_idx = (df_lecture["開講期"] == i) & df_lecture["連続数"].notnull()
        df_continuous = df_lecture[continuous_idx]
        make_constraints(save_dir, df_continuous, df_room, periods, is_continuous=True)

        # マッピングに関しては現状では連続の制約を組めていないため、1コマの割り当て問題として解く(連続部分は後処理で追加)
        df_continuous.loc[:, "コマ数"] = 1
        df_continuous.to_csv(
            save_dir.joinpath(f"lecture_properties.csv"),
            index=False,
            header=True,
            encoding="utf-8",
        )
        codes = df_continuous["授業コード"].to_list()
        if codes:
            make_mappings(save_dir, df_continuous, codes)
        else:
            print("There is no continuous lecture.")
