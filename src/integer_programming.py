import csv
import json
import time
from pathlib import Path
from typing import Dict, List

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
        return sorted(sum(content, []))

def read_csv(file_path: Path) -> 

def read_json(file_path: Path) -> Dict[str, str]:
    """
    jsonを読み込んで返す関数.

    Args:
        file_path (Path): ファイルパス

    Returns:
        Dict[str, str]: 辞書
    """
    with open(file_path, encoding='utf-8') as f:
        content = json.load(f)
    return content

if __name__ == '__main__':
    DATA_DIR = Path(__file__).parents[1].joinpath('data', 'first')
    
    # 集合の読み込み
    subjects = read_one_col_csv(DATA_DIR.joinpath('subjects.csv'))
    periods = read_one_col_csv(DATA_DIR.joinpath('periods.csv'))
    rooms = read_one_col_csv(DATA_DIR.joinpath('rooms.csv'))
    courses = read_one_col_csv(DATA_DIR.joinpath('courses.csv'))
    teachers = read_one_col_csv(DATA_DIR.joinpath('teachers.csv'))
    
    # 授業情報(辞書)の読み込み
    subject_propaties = read_json(DATA_DIR.joinpath('subject_propaties.json'))
    teacher_lectures = read_json(DATA_DIR.joinpath('teacher_lectures.json'))
    course_lectures = read_json(DATA_DIR.joinpath('course_lectures.json'))
    
    # # 制約の読み込み
    # CONSTRAINS_DIR = DATA_DIR.joinpath('constrains')
    # sr_map = read_csv(CONSTRAINS_DIR.joinpath('sr_map.csv'))
    # rp_map = read_csv(CONSTRAINS_DIR.joinpath('rp_map.csv'))
    # tp_map = read_csv(CONSTRAINS_DIR.joinpath('tp_map.csv'))
    # sp_map = read_csv(CONSTRAINS_DIR.joinpath('sp_map.csv'))
    # cp_map = read_csv(CONSTRAINS_DIR.joinpath('cp_map.csv'))
    
    print()
