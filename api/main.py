import shutil
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# テンプレートと静的ファイルの準備
BASE_DIR = Path(__file__).resolve().parent
print(str(Path(BASE_DIR.parent, 'outputs')))
app.mount('/static', StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name='static')
app.mount('/outputs', StaticFiles(directory=str(Path(BASE_DIR.parent, 'outputs'))), name='outputs')
templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))

@app.get('/test')
async def hello():
    """ 動作チェック用のエンドポイント """
    return {'message': 'ChronoScheduler is running!'}

@app.get('/', response_class=HTMLResponse)
async def index(request: Request, solution_html = None):
    """ メインページのエンドポイント. ファイルのアップロードを行う. """
    query_dict = {
        'request': request,
        'solution_html': solution_html
    }
    return templates.TemplateResponse('index.html', query_dict)

@app.post('/', response_class=HTMLResponse)
async def index(request: Request, solution_html = None):
    """ メインページのエンドポイント. 何もファイルが選択されずに送信ボタンがクリックされた場合. """
    query_dict = {
        'request': request,
        'solution_html': solution_html
    }
    return templates.TemplateResponse('index.html', query_dict)

@app.post('/solve', response_class=HTMLResponse)
async def solve(request: Request, uploaded_files: list[UploadFile] = None):
    """ メインページのエンドポイント. アップロードされたデータを保存し、数理最適化を行う. """
    # データがアップロードされていなければトップページにリダイレクト
    if not uploaded_files[0].filename:
        return RedirectResponse(url='http://localhost:8000/')
    else:
        # アップロードされたファイルを保存
        save_dir = BASE_DIR.parent.joinpath('data', 'uploaded')
        save_dir.mkdir(parents=True, exist_ok=True)
        for uploaded_file in uploaded_files:
            with open(save_dir.joinpath(uploaded_file.filename), 'wb+') as f:
                shutil.copyfileobj(uploaded_file.file, f)
        
        # TODO: 最適化を実行
        solution_html = '<p>This is a test</p>'
        
        query_dict = {
        'request': request,
        'solution_html': solution_html
        }
        
        # TODO: index.htmlに最適化後の時間割を表示(index.htmlに追記)
        # TODO: index.htmlに/timetableへのリンクを作成(結果をフィルタリングボタンでリンクを追加)
        
        return templates.TemplateResponse('index.html', query_dict)

@app.get('/timetable', response_class=HTMLResponse)
async def view_result(request: Request,
                      course: str = None,
                      category: str = None,
                      teacher: str = None,
                      room: str = None,
                      period: str = None):
    """ 最適化後の時間割を表示するエンドポイント """
    root_dir = Path(__file__).parents[1]
    data_dir = root_dir.joinpath('data', 'toy')
    output_dir = root_dir.joinpath('outputs', 'toy')
    
    # 最適化した時間割データの読み込み
    cols = ['授業コード', '講義名', '対象コース', '種別', '担当教員', '教室', '時限', 'コマ数', '推定受講者数']
    df = pd.read_csv(output_dir.joinpath('result.csv'), header=None, names=cols)
    
    # 各集合の作成
    courses = set(sum([cs.strip().split(',') for cs in df['対象コース'].to_list()], []))
    categories = set(df['種別'].to_list())
    teachers = set(sum([ts.strip().split(',') for ts in df['担当教員'].to_list()], []))
    rooms = pd.read_csv(data_dir.joinpath('rooms.csv'))['教室'].to_list()
    periods = pd.read_csv(data_dir.joinpath('periods.csv'), header=None).iloc[0].to_list()
    
    # 対象コース/種別/担当教員/教室/時限でそれぞれフィルタリング
    if course:
        df = df[df['対象コース'].str.contains(course)]
    if category:
        df = df[df['種別'] == category]
    if teacher:
        df = df[df['担当教員'].str.contains(teacher)]
    if room:
        df = df[df['教室'] == room]
    if period:
        df = df[df['時限'] == period]
    
    df_html = df.sort_values(by=['時限']).to_html(index=False)
    
    # TODO: よくみる時間割の表形式に並べて表示、ダウンロードボタンでcsvまたはexcelで保存できるように
    
    query_dict = {
        'request': request,
        'df_html': df_html,
        'courses': sorted(list(courses)),
        'categories': categories,
        'teachers': sorted(list(teachers)),
        'rooms': rooms,
        'periods': periods}
    
    return templates.TemplateResponse('result.html', query_dict)

@app.get('/download/{name}', response_class=FileResponse)
async def download_file(name: str):
    """ ファイルをダウンロードするエンドポイント """
    path = BASE_DIR.parent.joinpath(f'outputs/{name}')
    return path
