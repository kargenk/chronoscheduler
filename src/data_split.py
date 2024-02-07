from pathlib import Path

import pandas as pd

if __name__ == '__main__':
    DATA_DIR = Path(__file__).parents[1].joinpath('data', 'kiu')
    semesters = ['first', 'second']
    targets = [[1, 3], [2]]
    
    df_lecture = pd.read_csv(DATA_DIR.joinpath('lecture_properties.csv'))
    
    for semester, target in zip(semesters, targets):
        save_dir = DATA_DIR.joinpath(semester)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        _df = df_lecture[df_lecture['開講期'].isin(target)]
        _df.to_csv(save_dir.joinpath('lecture_properties.csv'), encoding='utf-8-sig', index=False)
        print(f'{semester.capitalize()}: {len(_df)}')
    
    print(f'[Success] File is Splitted to "{DATA_DIR}" first and second.')
