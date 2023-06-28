from pathlib import Path

import pandas as pd

if __name__ == '__main__':
    ROOT_DIR = Path(__file__).parents[1]
    DATA_DIR = ROOT_DIR.joinpath('data', 'toy')
    OUTPUT_DIR = ROOT_DIR.joinpath('outputs', 'toy')
    
    # 最適化された時間割データの読み込み
    cols = ['授業コード', '講義名', '種別', '対象コース', '担当教員', '教室', '時限', 'コマ数', '推定受講者数']
    df = pd.read_csv(OUTPUT_DIR.joinpath('result.csv'), header=None, names=cols)
    periods = pd.read_csv(DATA_DIR.joinpath('periods.csv')).columns.to_list()
    
    # 時限毎にサブセットに分け、最終出力形式のテーブルになるように空行を追加する
    df_subsets = {}
    max_len = df['時限'].value_counts().max()
    empty_sample = pd.Series({}, dtype=object)
    for period in periods:
        df_subset = df[df['時限'] == period]
        blank_data = [empty_sample for _ in range(len(df_subset), max_len + 1)]
        df_subset = pd.concat([df_subset, pd.DataFrame(blank_data)])
        df_subsets[period] = df_subset.reset_index(drop=True).sort_values(by='授業コード')
    
    # 最終出力形式のような多層インデックスのデータフレームを作成
    time_slots = [str(i) + '限' for i in range(1, 6)]
    days = ['月', '火', '水', '木', '金', '土']
    multi_cols = pd.MultiIndex.from_product([days, cols])
    multi_idx = pd.MultiIndex.from_product([time_slots, range(max_len + 1)], names=['時限', '講義数'])
    df_output = pd.DataFrame(index=multi_idx, columns=multi_cols)
    for ts in time_slots:
        for day in days:
            df_output.loc[ts, day] = df_subsets[day + ts.replace('限', '')].to_numpy()
    # 不必要なインデックスを削除
    df_output = df_output.reset_index(level='講義数', drop=True)
    df_output.to_csv(OUTPUT_DIR.joinpath('timetable.csv'), encoding='cp932')
