import csv
import json
import multiprocessing
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pulp
from tqdm import tqdm


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
        cols (List[str]): 制約条件カラム名のリスト.

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
    global subjects
    global teachers
    # 辞書
    global course_lectures
    global teacher_lectures
    global subject_propaties
    # 制約
    global cp_map
    global pr_map
    global sp_map
    global sr_map
    global tp_map
    
    ##### 物理的な制約 #####
    
    # 基本制約: 同じ時間の同じ教室に複数の授業を割り当てない
    for p in periods:
        for r in rooms:
            problem += pulp.lpSum(x[s, p, r] for s in subjects) <=1, f'基本制約_{p}_{r}'
    
    # 教員制約: 教員は同じ時間に複数の授業を行えない
    for t in teachers:
        for p in periods:
            problem += pulp.lpSum(x[s, p, r] for s in teacher_lectures[t] for r in rooms) <= 1, f'教員制約_{t}_{p}'
    
    # 授業教室制約: 授業は使用できる教室が限られている
    for s in subjects:
        for p in periods:
            for r in rooms:
                problem += x[s, p, r] <= sr_map.loc[s, r], f'授業教室制約_{s}_{p}_{r}'
    
    # TODO: クラスを学年、組にまで細分化して再定義 -> 学年、組における包含関係をどう扱うかが問題
    # # クラス基本制約: クラスは同じ時間に複数の授業を受けられない
    # # (被りありに制約を緩和しないとInfeasible: 実行不可能)
    # for c in courses:
    #     for p in periods:
    #         problem += pulp.lpSum(x[s, p, r] for s in course_lectures[c] for r in rooms) <= 1, f'クラス基本制約_{c}_{p}'
    
    ##### 制約 #####
    
    # TODO: 「クラスは同じ時間に複数の必須授業を受けられない」制約
    
    # 授業コマ数制約: 授業は指定されたコマ数回実施する必要がある
    for s in subjects:
        problem += pulp.lpSum(x[s, p, r] for p in periods for r in rooms) == subject_propaties[s][6], f'授業コマ数制約_{s}'
    
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
    global subjects
    
    problem += pulp.lpSum(x[s, p, r]
                          for s in subjects
                          for p in periods
                          for r in rooms), '仮の目的関数: 決定した授業数'

def describe() -> None:
    """ 最適化問題の変数の数と制約の数を出力する. """
    global problem
    
    print('整数計画法を用いた時間割最適化問題')
    print('-' * 30)
    vals = problem.variables()
    constrains = problem.constraints
    print(f'変数: {len(vals)}, 制約: {len(constrains)}')
    print('-' * 30)
    
    # print(problem)

if __name__ == '__main__':
    departments = ['M', 'E', 'C', 'V', 'R', 'H', 'B', 'I', 'N', 'D', 'U', 'L', 'A']
    semesters = ['first', 'second']
    for department in tqdm(departments[1:]):
        for semester in semesters:
            data_dir = Path(__file__).parents[1].joinpath('data', department, semester)
            constraints_dir = data_dir.joinpath('constrains')
            output_dir = Path(__file__).parents[1].joinpath('outputs', department, semester)
            output_dir.mkdir(parents=True, exist_ok=True)
            num_cores = multiprocessing.cpu_count()
            
            # 集合の読み込み
            subjects = read_one_col_csv(data_dir.joinpath('subjects.csv'))
            periods = read_one_col_csv(data_dir.joinpath('periods.csv'))
            rooms = read_one_col_csv(data_dir.joinpath('rooms.csv'))
            courses = read_one_col_csv(data_dir.joinpath('courses.csv'))
            teachers = read_one_col_csv(data_dir.joinpath('teachers.csv'))
            
            # 授業情報(辞書)の読み込み
            subject_propaties = read_json(data_dir.joinpath('subject_propaties.json'))
            teacher_lectures = read_json(data_dir.joinpath('teacher_lectures.json'))
            course_lectures = read_json(data_dir.joinpath('course_lectures.json'))
            
            # 制約の読み込み
            sr_map = read_json(constraints_dir.joinpath('sr_map.json'), is_constrain=True, cols=rooms)
            pr_map = read_json(constraints_dir.joinpath('pr_map.json'), is_constrain=True, cols=rooms)
            tp_map = read_json(constraints_dir.joinpath('tp_map.json'), is_constrain=True, cols=periods)
            sp_map = read_json(constraints_dir.joinpath('sp_map.json'), is_constrain=True, cols=periods)
            cp_map = read_json(constraints_dir.joinpath('cp_map.json'), is_constrain=True, cols=periods)
            
            # 最大化問題を定義
            problem = pulp.LpProblem(name='lp', sense=pulp.LpMaximize)
            
            # 変数の定義
            x = {}
            for s in subjects:
                for p in periods:
                    for r in rooms:
                        x[s, p, r] = pulp.LpVariable(f'x({s}, {p}, {r})', 0, 1, pulp.LpInteger)

            # 制約条件, 目的関数を定義して問題のサイズを出力
            define_constraints()
            define_objective()
            describe()
            
            # 解く
            # print(pulp.pulpTestAll())  # 使用できるソルバ一覧, デフォルトはsite-packages\pulp\solverdir\cbc\win\64\cbc.exe
            solver = pulp.COIN_CMD(msg=1, threads=num_cores)  # timeLimit=24*60*60
            time_start = time.perf_counter()
            status = problem.solve()
            time_end = time.perf_counter()
            objective = pulp.value(problem.objective)  # 理想は授業コード数(前期は227)
            print(f'Status: {pulp.LpStatus[status]}, Time: {time_end - time_start} [sec]')
            print(f'objective: {objective}')
            
            # 解が得られれば出力
            if pulp.LpStatus[status] == 'Optimal':
                with open(output_dir.joinpath('result.csv'), 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    contents = []
                    for r in rooms:
                        for p in periods:
                            for s in subjects:
                                if x[s, p, r].value() > 0.5:
                                    sp = subject_propaties[s]
                                    # [授業コード, 講義名, 講師, 部屋, 時限, コース, 学年, 組, 種別, コマ数]
                                    content = [s, sp[0], sp[1], r, p, sp[2], sp[3], sp[4], sp[5], sp[6]]
                                    contents.append(content)
                    writer.writerows(contents)