from pathlib import Path

if __name__ == '__main__':
    # TODO: outputs/zerothの結果から、講義情報を更新
    DATA_DIR = Path(__file__).parents[1].joinpath('data', 'toy', 'first')
    print(DATA_DIR)
