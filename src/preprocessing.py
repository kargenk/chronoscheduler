import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd


def get_facility(file_path: Path) -> pd.DataFrame:
    """
    施設情報を読み込む関数.

    Args:
        file_path (Path): 施設情報のファイルパス

    Returns:
        pd.DataFrame: 施設情報のデータフレーム
    """
    df_facility = pd.read_csv(file_path)
    # 建物と部屋番号から部屋の名前を作成
    df_facility['施設名'] = df_facility['施設名'].str.cat(df_facility['講義室'], sep='_').unique().tolist()
    return df_facility

def get_dfs(files_path: List[Path]) -> Dict[str, pd.DataFrame]:
    """
    複数のエクセルファイルからデータフレームを作成する関数.

    Args:
        files_path (List[Path]): エクセルファイルのパスリスト

    Returns:
        Dict[str, pd.DataFrame]: データフレーム
    """
    global pattern
    
    dfs = {}
    for file_path in files_path:
        df = pd.read_excel(file_path, sheet_name=1)                                # 0番目(X科)は時間割の神エクセル、1番目(Sheet1)がシラバス形式
        df['授業コード'] = df['授業コード'].astype(str).apply(lambda x: x.zfill(4))  # 授業コードは左ゼロ埋めで4桁
        df['開講期'] = df['開講期'].astype(np.int8)
        df['必選'] = df['必選'].astype(str).apply(lambda x: x.replace('○◎', '◎'))  # 「○◎」はよくわからんのでいったん必須(◎)とする
        df['コマ数'] = df['コマ数'].astype(np.int8)
        df['ｺｰｽ'] = df['ｺｰｽ'].fillna('all').astype(str).apply(lambda x: x.strip())  # \u3000(全角スペース)が含まれているので除去
        df['学年'] = df['学年'].astype(str).apply(lambda x: x.replace('・', '&'))   # 数値と文字列が混在しているので文字列に統一
        df['ｸﾗｽ'] = df['ｸﾗｽ'].fillna('all')                                         # 何も記載がないものは全員が対象(all)とする
        key = pattern.findall(str(file_path.name))[0]
        dfs[key] = df

    return dfs

def define_main_sets(df: pd.DataFrame) -> Tuple[Set[str], Set[int], Set[str], Set[str], Set[str]]:
    """
    各集合を定義する関数.

    Args:
        df (pd.DataFrame): データフレーム

    Returns:
        Tuple[Set[str], Set[int], Set[str], Set[str], Set[str]]: 授業, 時限, 部屋, クラス, 教員の集合
    """
    global df_facility
    
    # 授業のリスト
    subjects = df['授業コード'].unique().tolist()
    
    # 時限のリスト
    weekdays = ['月', '火', '水', '木', '金', '土']
    times = [str(t) for t in range(1, 6)]
    periods = [w + t for w in weekdays for t in times]
    
    # 教室のリスト
    rooms = df_facility['施設名'].str.cat(df_facility['講義室'], sep='_').unique().tolist()
    
    # クラスの集合
    # 厳密ではないが、まずはコースをクラスと考える
    cs = df['ｺｰｽ'].unique().tolist()
    courses = set(sum([pattern.findall(c) for c in cs], []))
    
    # 担当教員の集合
    teachers = set(sum(df['teachers'].tolist(), []))
    teachers.discard('師玉')  # おそらく師玉真or師玉礼だと思われるので削除
    
    return set(subjects), set(periods), set(rooms), courses, teachers

def define_main_dicts(df: pd.DataFrame) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]:
    """
    各辞書を定義する関数.

    Args:
        df (pd.DataFrame): _description_

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]: 
            授業の辞書{code: [授業名,科目担当,コマ数,クラス]}, 科目担当の辞書{teacher: lecture_list}, クラス授業の辞書{class: lecture_list}
    """
    global pattern
    
    subject_propaties = defaultdict(list)
    teacher_lectures = defaultdict(list)
    course_lectures = defaultdict(list)
    for code in subjects:
        data = df[df['授業コード'] == code]
        _, lecture_name, _, _, duration, _courses, _, _, _, _teachers = data.values[0]
        # 講義名の英数字は半角にカタカナは全角化、不要な空白は除去
        lecture_name = unicodedata.normalize('NFKC', lecture_name.title().strip())
        # 授業辞書
        subject_propaties[code] = [lecture_name, _teachers, duration, _courses]
        # 科目担当辞書
        for teacher in _teachers:
            teacher_lectures[teacher].append(code)
        # クラス授業辞書
        cs = set(sum([pattern.findall(c) for c in _courses], []))
        for c in cs:
            course_lectures[c].append(code)
    
    return subject_propaties, teacher_lectures, course_lectures

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    前処理(重複を削除, 教員のいないデータを除外, 無駄な記号や空白の削除)を行う関数.

    Args:
        df (pd.DataFrame): データフレーム

    Returns:
        pd.DataFrame: 前処理後のデータフレーム
    """
    global pattern
    
    # 授業コードが重複しているサンプルに対して、コースを統合
    id_duplicates = df[df.duplicated(subset=('授業コード'))]['授業コード']
    for id_dup in id_duplicates:
        targets = (df['授業コード'] == id_dup)
        cs = df[df['授業コード'] == id_dup]['ｺｰｽ'].tolist()
        # 重複している講義のコースリストからコース(大文字アルファベット一文字)を抜き出して重複コースを削除
        course_set = set(sum([pattern.findall(c) for c in cs], []))
        # 先頭のみを指定しようとしてilocでアクセスすると警告なしのChain Indexingで元のdfが変更されないので両方とも変更
        df.loc[targets, ['ｺｰｽ']] = '・'.join(list(course_set))

    # 授業コードが重複しているレコードを削除
    # 1096: 機械工学プロジェクトⅡと1097: 機械工学プロジェクトⅡは同じカラムがあり、後ろの方にのみ講師情報があるので後ろを残す
    df.drop_duplicates(subset=('授業コード'), inplace=True, keep='last')
    
    # 教員が存在しない講義(例: Academic English for Global leaders系)はわからないのでいったん除去
    df = df.dropna(subset=['教員名']).copy()
    
    # 正規表現で無駄な記号や空白を除去
    garbage = re.compile('[!"#$%&\'\\\\()*+-./:;<=>?@[\\]^_`{|}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。、？！｀＋￥％]')
    teachers_raw = df['教員名'].tolist()
    teachers_clean = [re.sub(garbage, ',', s).replace('\u3000', '').strip(',').strip() for s in teachers_raw]

    df['teachers'] = [tc.split(',') for tc in teachers_clean]
    df = df.drop(columns=['教員名'])

    return df

def define_constrains(df: pd.DataFrame) -> Tuple[Dict[str, Any]]:
    """
    制約を定義する関数.

    Args:
        df (pd.DataFrame): データフレーム

    Returns:
        Tuple[Dict[str, Any]]: 制約
    """
    global df_facility
    # room_capacity = dict(zip(df_facility['施設名'], df_facility['最大席数']))
    
    ### sr_map: 授業sが教室rで利用可能かを表す01行列
    # 講義数の重複数で定員数を割った値で人数の欠損値を補完
    # M科: 機械工学コースの入学時の定員は180人(ref. https://op.kait.jp/admission/recruit/)
    num_max = 180
    dup_count = df.pivot_table(index=['授業科目'], aggfunc='size').to_dict()
    df.loc[:, '最大人数'] = df.apply(lambda df: num_max / dup_count[df['授業科目']]
                                            if pd.isnull(df['最大人数']) else df['最大人数'], axis=1)
    
    num_subjects = len(df)
    num_rooms = len(df_facility)
    sr_map = defaultdict(lambda: np.zeros(num_rooms, dtype=np.int8))

    # 行が授業、列が部屋の01行列を作成
    room_cap = df_facility['最大席数'].values.astype(int)
    sr_mat = np.tile(room_cap, (num_subjects, 1))
    sr_mat = (df['最大人数'].values <= sr_mat.T).T.astype(np.int8)  # ブロードキャストするため、増やす次元を先頭にしてから再度戻す
    assert sr_mat.shape == (num_subjects, num_rooms)

    # 授業コードをkey, その部屋群が使用可(1) or 不可(0)をvalueとする辞書
    for i, subject in enumerate(df['授業コード']):
        sr_map[subject] = sr_mat[i]
    
    ### pr_map: 時限pに教室rが利用可能かを表す01行列
    pr_map = defaultdict(lambda: np.ones(num_rooms, dtype=np.int8))
    for p in periods:
        pr_map[p] = np.ones(num_rooms, dtype=np.int8)
    
    ### tp_map: 教員tが時限pに授業可能かを表す01行列
    num_periods = len(periods)
    tp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for t in teachers:
        tp_map[t] = np.ones(num_periods, dtype=np.int8)
    
    ### sp_map: 授業sが時限pに実施可能かを表す01行列
    sp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for s in subjects:
        sp_map[s] = np.ones(num_periods, dtype=np.int8)
    
    ### cp_map: コースcが時限pに授業可能かを表す01行列
    cp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for c in courses:
        cp_map[c] = np.ones(num_periods, dtype=np.int8)
    
    return sr_map, pr_map, tp_map, sp_map, cp_map

if __name__ == '__main__':
    DATA_DIR = Path(__file__).parents[1].joinpath('data')
    files_path = list(DATA_DIR.joinpath('timetable_2023').glob('*.xlsx'))
    pattern = re.compile('[A-Z]')
    
    # 施設情報の処理
    facility_path = DATA_DIR.joinpath('materials', 'facility.csv')
    df_facility = get_facility(facility_path)
    
    # データの読み込み
    dfs = get_dfs(files_path)
    df = dfs['M']
    df = preprocess(df)
    
    # 解空間を狭める(学期ごとに分割)
    ## 学期ごとに分割
    df_first = df[df['開講期'] == 1]
    df_second = df[df['開講期'] == 2]
    df_through = df[df['開講期'] == 3]
    assert len(df_first) + len(df_second) + len(df_through) == len(df)
    ## 必須と選択に分割
    df_required = df_first[df_first['必選'] == '◎']
    df_required_select = df_first[df_first['必選'] == '□']
    df_option = df_first[df_first['必選'] == '○']
    df_req_sel_re = df_first[df_first['必選'] == '■']
    assert len(df_required) + len(df_required_select) + len(df_option) + len(df_req_sel_re) == len(df_first)
    
    # 集合の定義
    subjects, periods, rooms, courses, teachers = define_main_sets(df_required)
    
    # 辞書の定義
    subject_propaties, teacher_lectures, course_lectures = define_main_dicts(df_required)

    # 制約の定義
    sr_map, pr_map, tp_map, sp_map, cp_map = define_constrains(df_required)
    
    # 集合をcsvで保存
    save_dir = DATA_DIR.joinpath('first', 'constrains')
    save_dir.mkdir(parents=True, exist_ok=True)

    file_names = ['subjects', 'periods', 'rooms', 'courses', 'teachers']
    sets = [subjects, periods, rooms, courses, teachers]
    for file_name, data in zip(file_names, sets):
        save_path = save_dir.parent.joinpath(f'{file_name}.csv')
        with open(save_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(sorted(list(data)))
    
    # 授業情報をjsonで保存
    dict_names = ['subject_propaties', 'teacher_lectures', 'course_lectures']
    dicts = [subject_propaties, teacher_lectures, course_lectures]
    for file_name, data in zip(dict_names, dicts):
        save_path = save_dir.parent.joinpath(f'{file_name}.json')
        with open(save_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 制約をjsonで保存
    file_names = ['sr_map', 'pr_map', 'tp_map', 'sp_map', 'cp_map']
    constrains = [sr_map, pr_map, tp_map, sp_map, cp_map]
    for file_name, data in zip(file_names, constrains):
        # NumPy配列はjson保存に非対応のためリストに変換
        for key, value in data.items():
            data[key] = value.tolist()
        save_path = save_dir.joinpath(f'{file_name}.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
