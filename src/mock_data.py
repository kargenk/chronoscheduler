import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def make_auxilialy_data(data_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    """
    時間割が決まっていない状態では授業情報に含まれないデータ群(部屋と時限)を作成して保存する.

    Args:
        data_dir (Path): 保存先のディレクトリ
    
    Returns:
        Tuple[pd.DataFrame, list[str]]: 部屋情報のデータフレームと時限リスト
    """
    # 部屋リスト
    buildings = list('ABCDEFG')
    nums = np.arange(1, 11)
    rooms = [f'{b}号館_{num:03d}' for b in buildings for num in nums]
    ## 許容人数を適当に決定
    capacities = np.full_like(rooms, 70)
    capacities[-7:] = 350
    capacities[-10:-7] = 200
    capacities[-20:-10] = 150
    capacities[-40:-20] = 100
    capacities[-45:-40] = 80
    capacities[:5] = 50
    # データフレームの形式で保存
    df_rooms = pd.DataFrame({'教室': rooms, '許容人数': capacities})
    df_rooms.to_csv(data_dir.joinpath('rooms.csv'), index=None)
    
    # 時間リスト
    days = ['月', '火', '水', '木', '金', '土']
    times = np.arange(1, 7)
    periods = [f'{d}{t}' for d in days for t in times]
    with open(data_dir.joinpath('periods.csv'), 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(periods)
    
    return df_rooms, periods

def make_main_data(data_dir: Path,
                   codes: list[str], names: list[str],
                   teacher_list: list[str], course_list: list[str]) -> pd.DataFrame:
    """
    メインとなる授業データを作成する.

    Args:
        data_dir (Path): 保存先のディレクトリ
        codes (list[str]): 授業コードのリスト
        names (list[str]): 講義名のリスト
        teacher_list (list[str]): 教員のリスト
        course_list (list[str]): コースのリスト
    
    Returns:
        pd.DataFrame: 作成したメインとなるデータフレーム
    """
    # 種別、(学年)、コマ数、推定受講人数、特定使用教室、開講期
    categories = ['必須', '選択']
    durations = np.arange(1, 4)
    num_students = [50, 70, 80, 100, 150, 200, 300]
    rooms = [None, 'E号館_007', 'F号館_006', 'G号館_005']
    semesters = [1, 2, 3]
    
    # ランダムに選択する際の確率
    prob_dur = [0.85, 0.14, 0.01]  # コマ数(1, 2, 3コマ)の割合
    prob_course = [0.40, 0.60]     # コース(1コースと複数コース)の割合
    prob_teacher = [0.85, 0.15]    # 講師人数(一人と複数人)の割合
    prob_room = [0.985, 5e-3, 5e-3, 5e-3]
    prob_semester = [0.5, 0.45, 0.05]
    # 推定受講人数(50, 70, 80, 100, 150, 200, 300人)の割合
    prob_students = [0.05, 0.50, 0.20, 0.15, 0.04, 0.04, 0.02]
    # 種別(必須と選択)の割合
    compulsory_ratio = 100 / len(codes)  # 必須を仮に100個とする
    # compulsory_ratio = 0.348
    prob_cat = [compulsory_ratio, 1 - compulsory_ratio]
    
    # モックデータをランダムに作成
    subject_properties = []
    for code, name in zip(codes, names):
        category = np.random.choice(categories, p=prob_cat)
        duration = np.random.choice(durations, p=prob_dur)
        num_expected = np.random.choice(num_students, p=prob_students)
        room = np.random.choice(rooms, p=prob_room)
        semester = np.random.choice(semesters, p=prob_semester)
        
        # コースの組み合わせを決定
        is_mix = (np.random.choice([True, False], p=prob_course))
        if is_mix:
            num_courses = np.random.randint(2, len(course_list) + 1)
            courses = np.random.choice(course_list, replace=False, size=num_courses)
        else:
            courses = [np.random.choice(course_list)]
        course = ','.join(courses)
        
        # 教員の人数を決定(複数人の場合は2~5人の中からランダムに選択)
        is_omunibus = (np.random.choice([True, False], p=prob_teacher))
        if is_omunibus:
            num_teachers = np.random.randint(2, 5)
            teachers = np.random.choice(teacher_list, replace=False, size=num_teachers)
        else:
            teachers = [np.random.choice(teacher_list)]
        teacher = ','.join(teachers)
        
        subject_property = [code, name, category, course, teacher, duration, num_expected, semester, room]
        subject_properties.append(subject_property)
    
    cols = ['授業コード', '講義名', '種別', '対象コース', '担当教員', 'コマ数', '推定受講者数', '開講期', '特定使用教室']
    df = pd.DataFrame(subject_properties, columns=cols)
    df.to_csv(data_dir.joinpath('lecture_properties.csv'), index=False, header=True)
    
    return df

def make_mappings(data_dir: Path, df: pd.DataFrame, codes: list[str]) -> None:
    """
    授業とコース、授業と教員の紐づけを行う.
    lecture_properties: 授業の情報
    teacher_lectures: 教員が受け持っている授業リスト
    course_lectures: コースが受ける全授業のリスト
    course_compulsory_lectures: コースが受けなければならない必修授業のリスト

    Args:
        data_dir (Path): 保存先ディレクトリ
        df (pd.DataFrame): 授業情報のデータフレーム
            ['授業コード', '講義名', '種別', '対象コース', '担当教員', 'コマ数', '推定受講者数', '開講期', '特定使用教室']
        codes (list[str]): 授業コードのリスト
    """
    teacher_lectures = defaultdict(list)
    course_lectures = defaultdict(list)
    course_compulsoly_lectures = defaultdict(list)
    for code in codes:
        data = df[df['授業コード'] == code]
        _, _, category, courses, teachers, _, _, _, _ = data.values[0]
        teachers = teachers.strip().split(',')
        courses = courses.strip().split(',')
        # 授業辞書
        keys = df['授業コード'].to_list()
        vals = df.drop(columns=['授業コード']).to_dict(orient='split')['data']
        lecture_properties = dict(zip(keys, vals))
        # 科目担当辞書
        for teacher in teachers:
            teacher_lectures[teacher].append(code)
        # クラス授業辞書
        for course in courses:
            course_lectures[course].append(code)
        # クラス必修授業辞書
        if category == '必須':
            for course in courses:
                course_compulsoly_lectures[course].append(code)
    
    # 紐づけ情報をjsonで保存
    dict_names = ['lecture_properties', 'teacher_lectures',
                  'course_lectures', 'course_compulsoly_lectures']
    dicts = [lecture_properties, teacher_lectures,
             course_lectures, course_compulsoly_lectures]
    for file_name, data in zip(dict_names, dicts):
        save_path = data_dir.joinpath(f'{file_name}.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def make_constraints(data_dir: Path,
                     df_lecture: pd.DataFrame,
                     df_room: pd.DataFrame,
                     periods: list[str]) -> tuple[dict[str, Any]]:
    """
    制約を定義する関数.
        lr_map: 授業lが教室rで利用可能かを表す01行列
        pr_map: 時限pに教室rが利用可能かを表す01行列
        tp_map: 教員tが時限pに授業可能かを表す01行列
        lp_map: 授業lが時限pに実施可能かを表す01行列
        cp_map: コースcが時限pに授業可能かを表す01行列

    Args:
        data_dir (Path): 保存先ディレクトリ
        df_lecture (pd.DataFrame): 授業のデータフレーム
        df_rooms (pd.DataFrame): 部屋のデータフレーム
        periods (list[str]): 時限のリスト

    Returns:
        Tuple[Dict[str, Any]]: 制約
    """
    save_dir = data_dir.joinpath('constraints')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    num_rooms = len(df_room)
    num_lectures = len(df_lecture)
    num_periods = len(periods)
    
    # 集合
    lectures = df_lecture['授業コード']
    teachers = set(sum([ts.strip().split(',')
                        for ts in df_lecture['担当教員'].to_list()], []))
    courses = set(sum([cs.strip().split(',')
                       for cs in df_lecture['対象コース'].to_list()], []))
    
    # 部屋名と順番のマッピング
    room2id = dict(zip(df_room['教室'], df_room.index))
    
    ### lr_map: 授業lが教室rで利用可能かを表す01行列
    lr_map = defaultdict(lambda: np.zeros(num_rooms, dtype=np.int8))
    # 行が授業、列が部屋の01行列を作成
    room_cap = df_room['許容人数'].values.astype(int)
    lr_mat = np.tile(room_cap, (num_lectures, 1))
    # ブロードキャストするため、増やす次元を先頭にしてから再度戻す
    lr_mat = (df_lecture['推定受講者数'].values <= lr_mat.T).T.astype(np.int8)
    assert lr_mat.shape == (num_lectures, num_rooms)
    # 授業コードをkey, その部屋群が使用可(1) or 不可(0)を表すNumPy配列をvalueとする辞書
    for i, code in enumerate(lectures):
        lr_map[code] = lr_mat[i]
    # TODO: semester=2(後期)の時に3(通期)で決まった講義の部屋/時限を固定にする処理
    # 指定教室がある場合その教室のみ利用可(1)に
    special_idx = df_lecture['特定使用教室'].notnull()
    for code, room in df_lecture[special_idx][['授業コード', '特定使用教室']].values:
        lr_map[code] = np.zeros_like(lr_map[code])
        lr_map[code][room2id[room]] = 1
    
    ### pr_map: 時限pに教室rが利用可能かを表す01行列
    pr_map = defaultdict(lambda: np.ones(num_rooms, dtype=np.int8))
    for p in periods:
        pr_map[p] = np.ones(num_rooms, dtype=np.int8)
    
    ### tp_map: 教員tが時限pに授業可能かを表す01行列
    tp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for t in teachers:
        tp_map[t] = np.ones(num_periods, dtype=np.int8)
    
    ### lp_map: 授業lが時限pに実施可能かを表す01行列
    lp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for l in lectures:
        lp_map[l] = np.ones(num_periods, dtype=np.int8)
    
    ### cp_map: コースcが時限pに授業可能かを表す01行列
    cp_map = defaultdict(lambda: np.ones(num_periods, dtype=np.int8))
    for c in courses:
        cp_map[c] = np.ones(num_periods, dtype=np.int8)
    
    # 各制約を保存
    file_names = ['lr_map', 'pr_map', 'tp_map', 'lp_map', 'cp_map']
    constrains = [lr_map, pr_map, tp_map, lp_map, cp_map]
    for file_name, data in zip(file_names, constrains):
        # NumPy配列はjson保存に非対応のためリストに変換
        for key, value in data.items():
            data[key] = value.tolist()
        save_path = save_dir.joinpath(f'{file_name}.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    np.random.seed(42)
    DATA_DIR = Path(__file__).parents[1].joinpath('data', 'toy')
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 授業と教員のリスト
    num_lectures = 500
    codes = [f'{code:04d}' for code in np.arange(1, num_lectures + 1)]
    names = [f'lecture_{name:04d}' for name in np.arange(1, num_lectures + 1)]
    teacher_list = ['天海', '如月', '星井', '萩原', '高槻', '菊池', '水瀬', '四条', '秋月', '三浦', '双海', '我那覇',
                    '春日', '最上', '伊吹', '田中', '島原', '佐竹', '所', '徳川', '箱崎', '野々原', '望月', '伴田', '七尾',
                    '高山', '松田', '高坂', '中谷', '天空橋', 'Stewart', '北沢', '舞浜', '木下', '矢吹', '横山', '二階堂', '馬場',
                    '大神', '豊川', '宮尾', '福田', '真壁', '篠宮', '百瀬', '永吉', '北上', '周防', 'Julia', '白石', '桜守',
                    '音無', '青羽', '高木', '黒井', 'gengen',
                    'professor_A', 'professor_B', 'professor_C', 'professor_D', 'professor_E', 'professor_F', 'professor_G',
                    'teacher_H', 'teacher_I', 'teacher_J', 'teacher_K', 'teacher_L', 'teacher_M', 'teacher_N']
    # 開講期(前期: 1、後期: 2)
    semesters = [1, 2]
    # クラスリスト
    course_list = ['AS', 'P', 'F', 'A']
    # groups = np.arange(1, 4)
    # classes = [f'{c}-{g}' for c in course_list for g in groups]
    
    df_room, periods = make_auxilialy_data(DATA_DIR)
    df_lecture = make_main_data(DATA_DIR, codes, names, teacher_list, course_list)
    for semester in semesters:
        if semester == 1:
            save_dir = DATA_DIR.joinpath('first')
            idx = df_lecture['開講期'].isin([1, 3])
        elif semester == 2:
            save_dir = DATA_DIR.joinpath('second')
            idx = df_lecture['開講期'].isin([2])
        save_dir.mkdir(parents=True, exist_ok=True)
        codes = df_lecture[idx]['授業コード'].to_list()
        
        df_lecture[idx].to_csv(save_dir.joinpath('lecture_properties.csv'), index=False, header=True)
        
        # 情報のマッピングと制約定義
        make_mappings(save_dir, df_lecture[idx], codes)
        make_constraints(save_dir, df_lecture[idx], df_room, periods)
