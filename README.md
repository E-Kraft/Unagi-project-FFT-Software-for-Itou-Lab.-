# フーリエ変換ver3.0シリーズ 解説書
***
## モジュールの解説
### NMR.py
NMRの生データファイルを読み込むために使用します。
(工事中)
***

## uvによる仮想環境構築
実行にはpythonの仮想環境を使うことをおすすめする。
ここではuvを使った仮想環境の構築方法について解説する。
> uvのインストールは[こちら](https://docs.astral.sh/uv/guides/install-python/)

### 環境のコピー
まずは開発者と同じ環境を各自のローカル環境に構築する。
- pyproject.toml
- uv.lock
- .python-version

以上3つを環境構築したいフォルダに移し、そのディレクトリで次のコマンドを実行する。
`uv sync`
自動的に.venvというフォルダが生成され、開発者と同じバージョンのpythonとライブラリが自動的にインストールされる。
どのライブラリがインストールされているかはpyproject.tomlに記載されている。

### 実行
`uv run python *.py`

### パッケージのインストール
`uv add パッケージ名`

### パッケージのアンインストール
`uv remove パッケージ名`

### pythonのバージョンを固定
固定すれば自動でそのバージョンのpythonがインストールされる。
pyproject.tomlの書き換えを必ず行うこと。
`uv python pin バージョン`

### nuitkaでexe化
`uv run nuitka --standalone --onefile --remove-output --follow-imports --plugin-enable=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icon2.ico *.py`  
tkinter,pyside6などはプラグインをオンにする必要あり
