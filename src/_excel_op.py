import csv
import json
from pathlib import Path

import pandas as pd


def json2xlsx(file_path: Path) -> None:
    """
    JSON形式の制約をExcel形式に変換する.

    Args:
        file_path (Path): 制約ファイルのパス.
                          仕様上*_map, *_lowers, *_uppersなど特定のファイル名である必要がある.
    """
    with open(file_path, 'r') as f:
        constraint = json.load(f)
    
    save_path = file_path.with_suffix('.xlsx')
    is_minmax = False if ('map' in str(file_path)) else True
    if is_minmax:
        col = '最小数' if ('lowers' in str(file_path)) else '最大数'
        df = pd.DataFrame(constraint.items(), columns=['時限', col])
        df.to_excel(save_path, index=False)
    else:
        idx = periods if (file_path.stem[1] == 'p') else rooms
        df = pd.DataFrame(constraint)
        df.index = idx
        df.to_excel(save_path)

def xlsx2json(file_path: Path) -> None:
    """
    Excel形式の制約をJSON形式に変換する.

    Args:
        file_path (Path): 制約ファイルのパス.
                          仕様上*_map, *_lowers, *_uppersなど特定のファイル名である必要がある.
    """
    save_path = file_path.with_suffix('.json')
    is_minmax = False if ('map' in str(file_path)) else True
    if is_minmax:
        col = '最小数' if ('lowers' in str(file_path)) else '最大数'
        df = pd.read_excel(file_path)
        data = dict(zip(df['時限'], df[col]))
    else:
        df = pd.read_excel(file_path, index_col=0)
        data = df.to_dict(orient='list')
    
    with open(save_path, 'w', encoding='utf-8-sig') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    data_dir = Path(__file__).parents[1].joinpath('data', 'toy')
    rooms = pd.read_csv(data_dir.joinpath('rooms.csv'))['教室'].to_list()
    with open(data_dir.joinpath('periods.csv'), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        periods = [row for row in reader]
        periods = sum(periods, [])
    
    # # JSON形式の制約をExcel形式に変換
    # file_list = data_dir.joinpath('first', 'constraints').glob('*.json')
    # for file_path in file_list:
    #     json2xlsx(file_path)
    
    # Excel形式の制約をJSON形式に変換
    file_list = data_dir.joinpath('first', 'constraints').glob('*.xlsx')
    for file_path in file_list:
        xlsx2json(file_path)
