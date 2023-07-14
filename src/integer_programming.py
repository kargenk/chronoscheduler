import csv
import json
import multiprocessing
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pulp


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
        return sum(content, [])

def read_json(file_path: Path, is_constraint: bool = False, cols: List[str] = None) -> Dict[str, Any]:
    """
    jsonを読み込んで返す関数.

    Args:
        file_path (Path): ファイルパス
        is_constraint (bool, optional): 制約条件フラグ. Defaults to False.
        cols (List[str]): 制約条件カラム名のリスト. Defaults to None.

    Returns:
        Dict[str, Any]: 辞書
    """
    with open(file_path, encoding='utf-8') as f:
        content = json.load(f)
    
    if is_constraint:
        for k, v in content.items():
            content[k] = np.array(v, dtype=np.int8)
        content = pd.DataFrame(content).transpose()
        content.columns = cols
    
    return content

class IPSolver(object):
    def __init__(self, root_dir: Path,
                 phase: str = 'zeroth_continuous',
                 semester: str = 'first',
                 solver_name: str = 'cbc'):
        
        # phase is 'zeroth_continuous' if pre-solve else ''
        
        # Directories
        self.root_dir = root_dir
        self.data_dir = self.root_dir.joinpath(phase, semester)
        self.constraints_dir = self.data_dir.joinpath('constraints')
        self.output_dir = self.root_dir.parents[1].joinpath('outputs', 'toy', phase, semester)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.solver_name = solver_name
        self.num_cores = multiprocessing.cpu_count()
    
    def _load_sets(self) -> None:
        # 集合の定義
        dtype = {'授業コード': str}
        df_lecture = pd.read_csv(self.data_dir.joinpath('lecture_properties.csv'), dtype=dtype)
        self.lectures = df_lecture['授業コード'].to_list()
        self.rooms = pd.read_csv(self.root_dir.joinpath('rooms.csv'))['教室'].to_list()
        self.periods = read_one_col_csv(self.root_dir.joinpath('periods.csv'))
        self.teachers = set(sum([ts.strip().split(',')
                                 for ts in df_lecture['担当教員'].to_list()], []))
        self.courses = set(sum([cs.strip().split(',')
                                for cs in df_lecture['対象コース'].to_list()], []))
    
    def _load_mappings(self) -> None:
        # 授業情報(辞書)の読み込み
        self.lecture_properties = read_json(self.data_dir.joinpath('lecture_properties.json'))
        self.teacher_lectures = read_json(self.data_dir.joinpath('teacher_lectures.json'))
        self.course_lectures = read_json(self.data_dir.joinpath('course_lectures.json'))
        self.course_compulsoly_lectures = read_json(self.data_dir.joinpath('course_compulsoly_lectures.json'))
    
    def _load_constraints(self) -> None:
        # 制約の読み込み
        self.lr_map = read_json(self.constraints_dir.joinpath('lr_map.json'),
                                is_constraint=True, cols=self.rooms)
        self.pr_map = read_json(self.constraints_dir.joinpath('pr_map.json'),
                                is_constraint=True, cols=self.rooms)
        self.tp_map = read_json(self.constraints_dir.joinpath('tp_map.json'),
                                is_constraint=True, cols=self.periods)
        self.lp_map = read_json(self.constraints_dir.joinpath('lp_map.json'),
                                is_constraint=True, cols=self.periods)
        self.cp_map = read_json(self.constraints_dir.joinpath('cp_map.json'),
                                is_constraint=True, cols=self.periods)
        self.p_lowers = read_json(self.constraints_dir.joinpath('p_lowers.json'))
        self.p_uppers = read_json(self.constraints_dir.joinpath('p_uppers.json'))
    
    def _define_constraints(self) -> None:
        """ 各制約を定義する. """
        
        ##### 物理的な制約 #####
        
        # 基本制約: 同じ時間の同じ教室に複数の授業を割り当てない
        for p in self.periods:
            for r in self.rooms:
                self.problem += pulp.lpSum(self.x[l, p, r] for l in self.lectures) <=1, f'基本制約_{p}_{r}'
        
        # 教員時限制約: 教員は同じ時間に複数の授業を行えない
        for t in self.teachers:
            for p in self.periods:
                self.problem += pulp.lpSum(self.x[l, p, r] for l in self.teacher_lectures[t] for r in self.rooms) <= self.tp_map.loc[t, p], f'教員制約_{t}_{p}'
        
        # 授業教室制約: 授業は使用できる教室が限られている
        for l in self.lectures:
            for p in self.periods:
                for r in self.rooms:
                    self.problem += self.x[l, p, r] <= self.lr_map.loc[l, r], f'授業教室制約_{l}_{p}_{r}'
        
        # # クラス基本制約: クラスは同じ時間に複数の授業を受けられない, ~高校用
        # # (大学レベルの講義数の場合、被りありに制約を緩和しないとInfeasible: 実行不可能)
        # for c in self.courses:
        #     for p in self.periods:
        #         self.problem += pulp.lpSum(self.x[l, p, r] for l in self.course_lectures[c] for r in self.rooms) <= 1, f'クラス基本制約_{c}_{p}'
        
        # 「クラスは同じ時間に複数の必須授業を受けられない」制約, 大学用
        if self.course_compulsoly_lectures:
            for c in self.courses:
                for p in self.periods:
                    self.problem += pulp.lpSum(self.x[l, p, r] for l in self.course_compulsoly_lectures[c] for r in self.rooms) <= 1, f'クラス基本制約_{c}_{p}'
        
        #- 授業時限制約: 授業は実施できる時限が限られている
        for l in self.lectures:
            for p in self.periods:
                for r in self.rooms:
                    self.problem += self.x[l, p, r] <= self.lp_map.loc[l, p], f'授業時限制約_{l}_{p}_{r}'
        
        #- 教室時限制約: 時限ごとに使用できる教室が決まっている
        for p in self.periods:
            for r in self.rooms:
                self.problem += pulp.lpSum(self.x[l, p, r] for l in self.lectures) <= self.pr_map.loc[p, r], f'教室時限制約_{r}_{p}'
        
        # TODO: 連続授業制約: 授業によっては連続した時限で行わなければならない
        
        ##### その他の制約 #####
        
        # 授業コマ数制約: 授業は指定されたコマ数回実施する必要がある
        for l in self.lectures:
            self.problem += pulp.lpSum(self.x[l, p, r] for p in self.periods for r in self.rooms) == self.lecture_properties[l][4], f'授業コマ数制約_{l}'
        
        # #- クラス時限制約: クラスは授業を受けられる時限が決まっている
        # for c in self.courses:
        #     for p in self.periods:
        #         self.problem += pulp.lpSum(self.x[s, p, r] for s in self.course_lectures[c] for r in self.rooms) >= self.cp_map.loc[c, p], f'クラス時限制約_{c}_{p}'
        
        ##### 要望による制約 #####
        
        # 曜日毎に科目の上限数を定める
        for p in self.periods:
            self.problem += pulp.lpSum(self.x[l, p, r] for l in self.lectures for r in self.rooms) >= self.p_lowers[p], f'時限最小授業数制約_{p}'
            self.problem += pulp.lpSum(self.x[l, p, r] for l in self.lectures for r in self.rooms) <= self.p_uppers[p], f'時限最大授業数制約_{p}'
    
    def _define_objective(self) -> None:
        """ 目的関数を定義. """
        self.problem += pulp.lpSum(self.x[l, p, r]
                                   for l in self.lectures
                                   for p in self.periods
                                   for r in self.rooms), '仮の目的関数: 決定した授業数'
    
    def _describe(self) -> None:
        """ 最適化問題の変数の数と制約の数を出力する. """
        print('整数計画法を用いた時間割最適化問題')
        print('-' * 30)
        vals = self.problem.variables()
        constraints = self.problem.constraints
        print(f'変数: {len(vals)}, 制約: {len(constraints)}')
        print('-' * 30)
        
        # print(self.problem)
    
    def define_problem(self) -> None:
        # 各種データ読み込み
        self._load_sets()
        self._load_mappings()
        self._load_constraints()
        
        # 最大化問題を定義
        self.problem = pulp.LpProblem(name='Timetable_Problem', sense=pulp.LpMaximize)
        
        # 決定変数の定義
        # 授業lが時限pに教室rで開講される場合1、されない場合0
        self.x = {}
        for l in self.lectures:
            for p in self.periods:
                for r in self.rooms:
                    self.x[l, p, r] = pulp.LpVariable(f'x({l}, {p}, {r})', 0, 1, pulp.LpInteger)
        
        # 制約条件, 目的関数を定義して問題のサイズを出力
        self._define_constraints()
        self._define_objective()
        self._describe()
    
    def solve(self) -> None:
        # 解く
        # pulp.pulpTestAll()
        # print(pulp.listSolvers(onlyAvailable=True))  # 使用できるソルバ一覧
        if self.solver_name == 'cbc':
            solver = pulp.PULP_CBC_CMD(msg=True, options=[f'threads={self.num_cores}'])
        elif self.solver_name == 'scip':
            solver = pulp.SCIP_CMD()
        time_start = time.perf_counter()
        status = self.problem.solve(solver)
        time_end = time.perf_counter()
        objective = pulp.value(self.problem.objective)  # 理想は総コマ数
        print(f'Status: {pulp.LpStatus[status]}, Time: {time_end - time_start} [sec]')
        print(f'objective: {objective}')
        
        # 解が得られれば出力
        if pulp.LpStatus[status] == 'Optimal':
            with open(self.output_dir.joinpath('result.csv'), 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                contents = []
                cols = ['授業コード', '講義名', '対象コース', '種別', '担当教員',
                        '教室', '時限', 'コマ数', '推定受講人数']
                contents.append(cols)
                for r in self.rooms:
                    for p in self.periods:
                        for l in self.lectures:
                            if self.x[l, p, r].value() > 0.5:
                                lp = self.lecture_properties[l]
                                content = [l, lp[0], lp[2], lp[1], lp[3], r, p, lp[4], lp[5]]
                                contents.append(content)
                writer.writerows(contents)

if __name__ == '__main__':
    ROOT_DIR = Path(__file__).parents[1].joinpath('data', 'toy')
    
    # phase is 'zeroth_continuous' if pre-solve else ''
    solver = IPSolver(ROOT_DIR, phase='', semester='first', solver_name='cbc')
    solver.define_problem()
    solver.solve()
