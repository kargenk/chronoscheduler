import csv
import json
import multiprocessing
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pulp

sys.path.append('../../solver/bin/')


def read_one_col_csv(file_path: Path) -> List[str]:
    """
    1カラムのcsvを読み込んでソート後、リストとして返す関数.

    Args:
        file_path (Path): ファイルパス

    Returns:
        List[str]: ソート後のリスト
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        content = [row for row in reader]
        return sorted(sum(content, []))

def read_json(file_path: Path, is_constrain: bool = False, cols: List[str] = None) -> Dict[str, Any]:
    """
    jsonを読み込んで返す関数.

    Args:
        file_path (Path): ファイルパス
        is_constrain (bool, optional): 制約条件フラグ. Defaults to False.
        cols (List[str]): 制約条件カラム名のリスト. Defaults to None.

    Returns:
        Dict[str, Any]: 辞書
    """
    with open(file_path, encoding='utf-8') as f:
        content = json.load(f)
    
    if is_constrain:
        for k, v in content.items():
            content[k] = np.array(v, dtype=np.int8)
        content = pd.DataFrame(content).transpose()
        content.columns = cols
    
    return content

def define_constraints() -> None:
    """ 各制約を定義する. """
    # 問題
    global problem
    # 集合
    global courses
    global periods
    global rooms
    global lectures
    global teachers
    # 辞書
    global course_lectures
    global course_compulsoly_lectures
    global teacher_lectures
    global lecture_properties
    # 制約
    global cp_map
    global pr_map
    global lp_map
    global lr_map
    global tp_map
    
    ##### 物理的な制約 #####
    
    # 基本制約: 同じ時間の同じ教室に複数の授業を割り当てない
    for p in periods:
        for r in rooms:
            problem += pulp.lpSum(x[l, p, r] for l in lectures) <=1, f'基本制約_{p}_{r}'
    
    # 教員制約: 教員は同じ時間に複数の授業を行えない
    for t in teachers:
        for p in periods:
            problem += pulp.lpSum(x[l, p, r] for l in teacher_lectures[t] for r in rooms) <= 1, f'教員制約_{t}_{p}'
    
    # 授業教室制約: 授業は使用できる教室が限られている
    for l in lectures:
        for p in periods:
            for r in rooms:
                problem += x[l, p, r] <= lr_map.loc[l, r], f'授業教室制約_{l}_{p}_{r}'
    
    # # クラス基本制約: クラスは同じ時間に複数の授業を受けられない, ~高校用
    # # (大学レベルの講義数の場合、被りありに制約を緩和しないとInfeasible: 実行不可能)
    # for c in courses:
    #     for p in periods:
    #         problem += pulp.lpSum(x[l, p, r] for l in course_lectures[c] for r in rooms) <= 1, f'クラス基本制約_{c}_{p}'
    
    # TODO: 「クラスは同じ時間に複数の必須授業を受けられない」制約, 大学用
    for c in courses:
        for p in periods:
            problem += pulp.lpSum(x[l, p, r] for l in course_compulsoly_lectures[c] for r in rooms) <= 1, f'クラス基本制約_{c}_{p}'
    
    ##### その他の制約 #####
    
    # 授業コマ数制約: 授業は指定されたコマ数回実施する必要がある
    for l in lectures:
        problem += pulp.lpSum(x[l, p, r] for p in periods for r in rooms) == lecture_properties[l][4], f'授業コマ数制約_{l}'
    
    # #- クラス時限制約: クラスは授業を受けられる時限が決まっている
    # for c in courses:
    #     for p in periods:
    #         problem += pulp.lpSum(x[s, p, r] for s in course_lectures[c] for r in rooms) >= cp_map.loc[c, p], f'クラス時限制約_{c}_{p}'
    
    ##### 要望による制約 #####
    
    # #- 授業時限制約: 授業は実施できる時限が限られている
    # for s in subjects:
    #     for p in periods:
    #         for r in rooms:
    #             problem += x[s, p, r] <= sp_map.loc[s, p], f'授業時限制約_{s}_{p}_{r}'
    
    # #- 教員時限制約: 教員は講義できる時限が決まっている
    # for t in teachers:
    #     for p in periods:
    #         problem += pulp.lpSum(x[s, p, r] for s in teacher_lectures[t] for r in rooms) <= tp_map.loc[t, p], f'教員時限制約_{t}_{p}'
    
    # #- 教室時限制約: 時限ごとに使用できる教室が決まっている
    # for p in periods:
    #     for r in rooms:
    #         problem += pulp.lpSum(x[s, p, r] for s in subjects) <= pr_map.loc[p, r], f'教室時限制約_{r}_{p}'

def define_objective() -> None:
    """ 目的関数を定義. """
    global problem
    
    global periods
    global rooms
    global lectures
    
    problem += pulp.lpSum(x[l, p, r]
                          for l in lectures
                          for p in periods
                          for r in rooms), '仮の目的関数: 決定した授業数'

def describe() -> None:
    """ 最適化問題の変数の数と制約の数を出力する. """
    global problem
    
    print('整数計画法を用いた時間割最適化問題')
    print('-' * 30)
    vals = problem.variables()
    constraints = problem.constraints
    print(f'変数: {len(vals)}, 制約: {len(constraints)}')
    print('-' * 30)
    
    # print(problem)

if __name__ == '__main__':
    data_dir = Path(__file__).parents[2].joinpath('data', 'toy')
    constraints_dir = data_dir.joinpath('constraints')
    output_dir = Path(__file__).parents[2].joinpath('outputs', 'toy')
    output_dir.mkdir(parents=True, exist_ok=True)
    num_cores = multiprocessing.cpu_count()
    
    # 集合の定義
    dtypes = {'授業コード': str}
    df_lecture = pd.read_csv(data_dir.joinpath('lecture_properties.csv'), dtype=dtypes)
    lectures = df_lecture['授業コード'].to_list()
    rooms = pd.read_csv(data_dir.joinpath('rooms.csv'))['教室'].to_list()
    periods = read_one_col_csv(data_dir.joinpath('periods.csv'))
    teachers = set(sum([ts.strip().split(',')
                        for ts in df_lecture['担当教員'].to_list()], []))
    courses = set(sum([cs.strip().split(',')
                       for cs in df_lecture['対象コース'].to_list()], []))
    
    # 授業情報(辞書)の読み込み
    lecture_properties = read_json(data_dir.joinpath('lecture_properties.json'))
    teacher_lectures = read_json(data_dir.joinpath('teacher_lectures.json'))
    course_lectures = read_json(data_dir.joinpath('course_lectures.json'))
    course_compulsoly_lectures = read_json(data_dir.joinpath('course_compulsoly_lectures.json'))
    
    # 制約の読み込み
    lr_map = read_json(constraints_dir.joinpath('lr_map.json'), is_constrain=True, cols=rooms)
    pr_map = read_json(constraints_dir.joinpath('pr_map.json'), is_constrain=True, cols=rooms)
    tp_map = read_json(constraints_dir.joinpath('tp_map.json'), is_constrain=True, cols=periods)
    lp_map = read_json(constraints_dir.joinpath('lp_map.json'), is_constrain=True, cols=periods)
    cp_map = read_json(constraints_dir.joinpath('cp_map.json'), is_constrain=True, cols=periods)
    
    # 最大化問題を定義
    problem = pulp.LpProblem(name='Timetable_Problem', sense=pulp.LpMaximize)
    
    # 決定変数の定義
    # 授業lが時限pに教室rで開講される場合1、されない場合0
    x = {}
    for l in lectures:
        for p in periods:
            for r in rooms:
                x[l, p, r] = pulp.LpVariable(f'x({l}, {p}, {r})', 0, 1, pulp.LpInteger)

    # 制約条件, 目的関数を定義して問題のサイズを出力
    define_constraints()
    define_objective()
    describe()
    
    # 解く
    # pulp.pulpTestAll()
    # print(pulp.listSolvers(onlyAvailable=True))  # 使用できるソルバ一覧
    # solver = pulp.COIN_CMD(path='../../solver/bin/cbc', msg=True, threads=num_cores, timeLimit=10)  # timeLimit=24*60*60
    # solver = pulp.PULP_CBC_CMD(msg=True, threads=num_cores, timeLimit=10)  # timeLimit=24*60*60
    time_start = time.perf_counter()
    status = problem.solve()
    time_end = time.perf_counter()
    objective = pulp.value(problem.objective)  # 理想は総コマ数(モックデータでは299)
    print(f'Status: {pulp.LpStatus[status]}, Time: {time_end - time_start} [sec]')
    print(f'objective: {objective}')
    
    # 解が得られれば出力
    if pulp.LpStatus[status] == 'Optimal':
        with open(output_dir.joinpath('result.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            contents = []
            for r in rooms:
                for p in periods:
                    for l in lectures:
                        if x[l, p, r].value() > 0.5:
                            lp = lecture_properties[l]
                            # ['授業コード', '講義名', '対象コース', '種別', '担当教員', '教室', '時限', 'コマ数', '推定受講人数']
                            content = [l, lp[0], lp[2], lp[1], lp[3], r, p, lp[4], lp[5]]
                            contents.append(content)
            writer.writerows(contents)
