from pathlib import Path

import numpy as np
import pandas as pd

if __name__ == '__main__':
    np.random.seed(42)
    DATA_DIR = Path(__file__).parents[1].joinpath('data', 'conventional')
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 大本のデータと先に連続授業に関して解いていた結果を読み込み
    df_lecture = pd.read_csv(DATA_DIR.joinpath('lecture_properties.csv'))
    df_result = pd.read_csv(DATA_DIR.joinpath('result.csv'))
    df_rooms = pd.read_csv(DATA_DIR.joinpath('rooms.csv'))
    
    ### 組の数だけ特定使用教室がカンマ区切りとして入力されている場合
    # 複数入力されているデータのみ抽出
    df_roomstr = df_lecture[df_lecture['特定使用教室'].str.contains(',', na=False)]
    idx = df_roomstr['授業コード'].values
    _rooms = df_roomstr['特定使用教室'].apply(lambda x: x.split(',')).to_list()
    id_to_room = dict(zip(idx, _rooms))
    
    # 教室を追加
    _df_result = df_result[df_result['授業コード'].isin(idx)]
    df_ex = pd.DataFrame(columns=_df_result.columns)
    for _, sample in _df_result.iterrows():
        for r in id_to_room[sample['授業コード']]:
            sample['教室'] = r
            _df = pd.DataFrame(sample.values, index=df_ex.columns).T
            df_ex = pd.concat([df_ex, _df], axis=0)
    
    ### 特定使用教室に数値のみが入っていた場合
    nums = [str(i) for i in range(1, 10)]
    df_roomint = df_lecture[df_lecture['特定使用教室'].isin(nums)]
    idx = df_roomint['授業コード'].values
    _df_result = df_result[df_result['授業コード'].isin(idx)]
    id_to_room = dict(zip(idx, df_roomint['特定使用教室'].astype(int).to_list()))
    # 使える部屋のリストからランダムに選択
    for _, sample in _df_result.iterrows():
        for _ in range(id_to_room[sample['授業コード']]):
            # TODO: 最小の教室を選ぶようにする
            rooms = df_rooms[df_rooms['許容人数'] >= sample['推定受講人数']]['教室'].to_list()
            sample['教室'] = np.random.choice(rooms, replace=False)  # 重複なし
            _df = pd.DataFrame(sample.values, index=df_ex.columns).T
            df_ex = pd.concat([df_ex, _df], axis=0)

    df_ex = df_ex.sort_values(by=['授業コード', '時限']).reset_index(drop=True)
    df_ex.to_csv(DATA_DIR.joinpath('class_fix.csv'),
                 index=False, encoding='utf-8-sig')
