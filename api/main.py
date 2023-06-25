from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# テンプレートと静的ファイルの準備
BASE_DIR = Path(__file__).resolve().parent
app.mount('/static', StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name='static')
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))

@app.get('/test')
async def hello():
    """ 動作チェック用のエンドポイント """
    return {'message': 'ChronoScheduler is running!'}

@app.get('/')
async def solve():
    """ メインページのエンドポイント """
    return {'message': 'ChronoScheduler is running!'}

@app.get('/timetable', response_class=HTMLResponse)
async def view_result(request: Request, category: str = None, classroom: str = None, period: str = None):
    # 最適化した時間割データの読み込み
    data_dir = Path(__file__).parents[1].joinpath('outputs', 'toy')
    cols = ['授業コード', '講義名', '対象コース', '種別', '担当教員', '教室', '時限', 'コマ数', '推定受講者数']
    df = pd.read_csv(data_dir.joinpath('result.csv'), header=None, names=cols)
    
    # TODO: 対象コース/種別/担当教員/教室/時限でそれぞれフィルタリングできるように、入力補完の機能もつけたい
    if category:
        df = df[df['種別'] == category]
    if classroom:
        df = df[df['教室'] == classroom]
    if period:
        df = df[df['時限'] == period]
    
    df_html = df.to_html(index=False)
    
    # TODO: よくみる時間割の表形式に並べて表示、ダウンロードボタンでcsvまたはexcelで保存できるように
    
    return templates.TemplateResponse('index.html', {'request': request, 'df_html': df_html})
