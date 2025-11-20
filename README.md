# uvコマンドの説明

## 実行
`uv run python *.py`

## パッケージのインストール
`uv add パッケージ名`

## パッケージのアンインストール
`uv remove パッケージ名`

## pythonのバージョンを固定
固定すれば自動でそのバージョンのpythonがインストールされる  
`pyproject.toml`の書き換えを必ず行う  
`uv python pin バージョン`

## nuitkaでexe化
`uv run nuitka --standalone --onefile --remove-output --follow-imports --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icon2.ico *.py`  
tkinter,pyside6などはプラグインをオンにする必要あり

## 環境のコピー
- `pyproject.toml`  
- `uv.lock`  
- `.python-version`  
以上3つを環境構築したいフォルダに移し、そのディレクトリで次のコマンドを実行  
`uv sync`
