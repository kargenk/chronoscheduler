import json
from pathlib import Path

import pandas as pd

from generate_mock_data import make_auxilialy_data, make_mappings
from integer_programming import read_json


def update_lecture_properties(data_dir: Path,
                              phase: str = 'zeroth_continuous',
                              semester: str = 'first') -> pd.DataFrame:
    """
    授業データを更新する.

    Args:
        data_dir (Path): データのあるディレクトリ
        phase (str): 問題の解く段階. Defaults to 'zeroth_continuous'.
        semester (str): 解く対象の期間. Defaults to 'first'.
    
    Returns:
        pd.DataFrame: fixした時間割情報
    """
    dtype = {'授業コード': str}

    # マスタデータの読み込み
    data_path = data_dir.joinpath('lecture_properties.csv')
    df = pd.read_csv(data_path, dtype=dtype)
    
    # サブ問題割り当て結果の読み込み
    result_path = data_dir.parents[2].joinpath(f'outputs/toy/{phase}/{semester}/result.csv')
    df_result = pd.read_csv(result_path, dtype=dtype)
    
    # # 割り当て済みの講義のみを抽出(コマ数はマスターデータにしかないため3コマ以上に対応する場合は必要)
    # fix_codes = df_result['授業コード'].to_list()
    # df_fix = df[df['授業コード'].isin(fix_codes)]
    
    # 割り当て結果を更新
    df_updated = df_result.copy()
    # 授業をコマ数分に拡張してデータを更新、ただし2コマまでしか対応していない
    df_updated['時限'] = df_updated['時限'].apply(lambda x: x[0] + str(int(x[1]) + 1))
    df_fix = pd.concat([df_result, df_updated], axis=0)
    df_fix = df_fix.sort_values(by=['授業コード', '時限']).reset_index(drop=True)
    df_fix.to_csv(result_path.parent.joinpath('fix.csv'),
                  index=False, encoding='utf-8-sig')
    
    # 次に解く問題のため割り当てた授業をデータから削除して更新
    df_result = df_result.set_index('授業コード')
    df = df.set_index('授業コード')
    df = df.drop(df_result.index, errors='ignore').reset_index()
    df.to_csv(data_path, index=False, encoding='utf-8-sig')
    # 授業辞書も更新
    codes = df['授業コード'].to_list()
    make_mappings(data_dir, df, codes)
    
    return df_fix

def update_constraints(constraints_dir: Path,
                       df_fix: pd.DataFrame,
                       rooms: list[str],
                       periods: list[str]) -> tuple[dict]:
    """
    授業が使用できる教室の制約を更新.
    cp_map: コース名をキー、時限の可否を1/0で表した数値列を値とする辞書.
    pr_map: 時限名をキー、教室の使用可否を1/0で表した数値列を値とする辞書.
    tp_map: 教員名をキー、時限の可否を1/0で表した数値列を値とする辞書.

    Args:
        constraints_dir (Path): 制約が保存されているディレクトリ
        df_fix (pd.DataFrame): fixした授業情報
        rooms (list[str]): 全ての部屋名リスト

    Returns:
        tuple[dict[str, list[int]],
              dict[str, list[int]],
              dict[str, list[int]]]: コースが受講できる時限一覧, 教室を使用できる時限一覧, 教員が授業できる時間一覧
    """
    cp_map = read_json(constraints_dir.joinpath('cp_map.json'),
                       is_constraint=True, cols=periods)
    pr_map = read_json(constraints_dir.joinpath('pr_map.json'),
                       is_constraint=True, cols=rooms)
    tp_map = read_json(constraints_dir.joinpath('tp_map.json'),
                       is_constraint=True, cols=periods)
    
    # 必須の科目があった場合、cp_mapを更新
    courses_list = df_fix[df_fix['種別'] == '必須']['対象コース'].to_list()
    ps = df_fix[df_fix['種別'] == '必須']['時限'].to_list()
    if ps and courses_list:
        for cs, p in zip(courses_list, ps):
            for c in cs.split(','):
                cp_map.loc[c, p] = 0
    
    # pr_mapの更新
    for p, r in zip(df_fix['時限'], df_fix['教室']):
        pr_map.loc[p, r] = 0
    
    # tp_mapの更新
    teachers_list = df_fix['担当教員'].to_list()
    ps = df_fix['時限'].to_list()
    for ts, p in zip(teachers_list, ps):
        for t in ts.split(','):
            tp_map.loc[t, p] = 0
    
    # for code in codes:
    #     pass
    #     # use_room = set(df_fix[df_fix['授業コード'] == code]['教室'].to_list()).pop()
    #     # lr_map.loc[code] = 0
    #     # lr_map.loc[code][use_room] = 1
        
    #     # TODO: cp_map, pr_map, tp_mapの更新
        
    #     # period = df_fix[df_fix['授業コード'] == code]['時限'].to_list()
    #     # print(code, period)
    
    names = ['cp_map', 'pr_map', 'tp_map']
    constraints = [cp_map, pr_map, tp_map]
    for name, constraint in zip(names, constraints):
        # 制約を保存用の形式に整形
        constraint = constraint.transpose()
        constraint =constraint.to_dict(orient='list')
        keys = constraint.keys()
        vals = list(constraint.values())
        constraint = dict(zip(keys, vals))
        
        # 各ファイルを上書きして更新
        save_path = constraints_dir.joinpath(f'{name}.json')
        for key, value in constraint.items():
            constraint[key] = value
        with open(save_path, 'w', encoding='utf-8-sig') as f:
            json.dump(constraint, f, ensure_ascii=False, indent=2)
    
    return cp_map, pr_map, tp_map

if __name__ == '__main__':
    phase = 'zeroth_continuous'
    semester = 'first'
    ROOT_DIR = Path(__file__).parents[1]
    data_dir = ROOT_DIR.joinpath(f'data/toy/{semester}')
    constraints_dir = data_dir.joinpath('constraints')
    
    df_room, periods = make_auxilialy_data()
    df_fix = update_lecture_properties(data_dir, phase=phase, semester=semester)
    rooms = df_room['教室'].to_list()
    cp_map, pr_map, tp_map = update_constraints(constraints_dir, df_fix, rooms, periods)
