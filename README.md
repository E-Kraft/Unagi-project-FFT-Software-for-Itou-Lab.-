# uvコマンドの説明

## 実行
uv run python main.py

## パッケージのインストール
uv add パッケージ名

## パッケージのアンインストール
uv remove パッケージ名

## pythonのバージョンを固定
固定すれば自動でそのバージョンのpythonがインストールされる、tomlの書き換えをお忘れなく
uv python pin バージョン

## nuitkaでexe化
uv run nuitka --standalone --onefile --remove-output --follow-imports --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icon2.ico main.py
tkinter,pyside6などはプラグインをオンにする必要あり

## 環境のコピー
pyproject.toml
uv.lock
.python-version
の以上3つを環境構築したいフォルダに移し、そのディレクトリで
uv sync
