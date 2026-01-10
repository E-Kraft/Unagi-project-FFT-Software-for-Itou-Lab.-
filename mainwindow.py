import sys
import os
import numpy as np
from PySide6.QtCore import Qt, QSize, QSettings, QUrl, QThread, QObject, Signal, qInstallMessageHandler, QtMsgType, qWarning, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidgetItem, QTreeWidgetItem,QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PySide6.QtUiTools import loadUiType
import pyqtgraph as pg
from qt_material import apply_stylesheet
import NMR
from datetime import datetime

# --- 初期設定 ---
settings = QSettings("FFTver3_series", "FFTver3.0") # アプリ終了後の設定保存用ファイル
pg.setConfigOptions(useOpenGL=True) #　グラフの描画にOpenGLを利用して高速化
pg.setConfigOption('foreground', 'k') #グラフを黒色に
Ui_MainWindow, _ = loadUiType("graphui.ui")

#デバッグモード用バージョン情報用--------------------------------------------------------------------------------------------------------------------------------------
#使用する場合はqInstallMessageHandler(qt_message_handler)とstdout / stderrのコメントをオフに
#コンソールの内容を受け取るクラス
class StdoutRedirect:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        if text.strip():
            now= datetime.now()
            self.widget.appendPlainText("")
            self.widget.appendPlainText(f"・{now.year}/{now.month}/{now.day} {now.hour}:{now.minute}:{now.second}")
            self.widget.appendPlainText(text)

    def flush(self):
        pass
def qt_message_handler(mode, context, message):
    # ここでは print するだけ
    print(message)

ABOUT_THIS_MD = """
# フーリエ変換Ver3シリーズ
- これは伊藤研究室で用いるNMR解析用フーリエ変換アプリです。
- これまで使われてきたフーリエ変換ver2.5の欠点を克服し、新たな機能を追加しています。
- 内容については順次更新します。
"""
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("このアプリについて")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setMarkdown(ABOUT_THIS_MD)
        browser.setOpenExternalLinks(True)

        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)

        layout.addWidget(browser)
        layout.addWidget(close_button)


VERSION_HISTORY_MD = """
# Ver3.0.0 β (2026/1/9)
- この項目を追加
"""

class VersionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("バージョン履歴")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setMarkdown(VERSION_HISTORY_MD)
        browser.setOpenExternalLinks(True)

        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)

        layout.addWidget(browser)
        layout.addWidget(close_button)


#--------------------------------------------------------------------------------------------------------------------------------------------------------



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #デバッグ用-----------------------------------------------------------------------------------------------------------------------------------
        # stdout / stderr を UI に流す
        #sys.stdout = StdoutRedirect(self.text_log)
        #sys.stderr = StdoutRedirect(self.text_log)

        # 動作確認用
        #print("Debug Mode Start!!")
        #--------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------ウィジェットの取得------------------------------------------------------------------
        self.dock = self.dockWidget
        self.text_log = self.textBrowser_widget_log
        self.plotWidget_sin = self.plot_widget_sin
        self.plotWidget_cos = self.plot_widget_cos
        self.plotWidget_norm = self.plot_widget_norm
        self.refer = self.button_widget_refer
        self.path_text = self.lineEdit_path
        self.button_select = self.pushButton_allselect
        self.button_next = self.pushButton_next
        self.button_before = self.pushButton_before
        self.list_import = self.list_View_import
        self.list_import.setIconSize(QSize(0, 0))
        self.list_data = self.treeWidget_data
        self.list_data.setHeaderLabels(["内部データ"])
        #メニューバー
        self.button_exit = self.action_exit
        self.button_git = self.action_GitHub
        self.button_read = self.action_read
        self.button_dock = self.action_dock
        self.button_ver = self.action_ver
        self.button_thisapp = self.action_thisapp
        self.button_default = self.action_size

        #初期化関数
        QTimer.singleShot(0, self.initial_function)

#--------------------------------------------------------コネクト------------------------------------------------------------------
        # --- クリック検出 ------------------
        self.refer.clicked.connect(self.select_folder) #　参照ボタン
        self.list_import.currentItemChanged.connect(self.filename_clicked) #ファイル名のアイテムがアクティブ化
        self.button_select.clicked.connect(self.all_select) # 全選択ボタン
        self.button_next.clicked.connect(self.next) # 次ボタン
        self.button_before.clicked.connect(self.before) # 前ボタン

        self.button_git.triggered.connect(self.open_github) # GitHubボタン
        self.button_exit.triggered.connect(self.quit_event) # 終了ボタン
        self.button_read.triggered.connect(self.select_folder) # 読み込みボタン
        self.button_dock.toggled.connect(self.dock.setVisible) # ドックの表示切り替えボタン
        self.dock.visibilityChanged.connect(self.button_dock.setChecked) # ドックのオン/オフの表示切り替え
        self.button_ver.triggered.connect(self.show_version_dialog) #バージョン履歴ボタン
        self.button_thisapp.triggered.connect(self.show_thisapp_dialog) #このアプリについて
        self.button_default.triggered.connect(self.resize_default)
        #self.plotWidget_sin.scene().sigMouseClicked.connect(self.onClick)
        #self.plotWidget_cos.scene().sigMouseClicked.connect(self.onClick)
        #self.plotWidget_norm.scene().sigMouseClicked.connect(self.onClick)

        # --- D&D検出 -------------------
        self.list_import.filesDropped.connect(self.DandD) # リストへのドラッグアンドドロップ




#-----------初期化-----------------------------------------------------------------------------------------------------------------------------------

    def initial_function(self):
        #--------------------------------------------------------ステータスバーの設定------------------------------------------------------------------
        self.statusBar().setStyleSheet("""
        QStatusBar{
        background-color: #f5f5f5;
        font-size: 14px;
        padding: 6px 8px;
        border-bottom: 1px solid #e0e0e0;
        }
        """)
        self.statusBar().showMessage("準備完了")

# ----------------------------------------------------- プロット表示 -----------------------------------------------------------------
        # --- データ準備 ---
        #zeropoint = 1400 #ゼロポイント
        #n_ind= 3441 #切り取り範囲(負)
        #p_ind = 4752 #切り取り範囲(正)
        #base_angle = np.pi / 100 #基本の位相回転角(フーリエ変換ver2.5参照)　optionで選択できるようにするかも

        #プロット初期設定
        self.plotWidget_sin.setLabel('left',"SIN",    **{'font-size': '12pt', 'color': 'k'})
        self.plotWidget_sin.setBackground("#FFFFFF00")
        self.plotWidget_sin.hideButtons()
        self.plotWidget_cos.setLabel('left',"COS",    **{'font-size': '12pt', 'color': 'k'})
        self.plotWidget_cos.setBackground("#FFFFFF00")
        self.plotWidget_cos.hideButtons()
        self.plotWidget_norm.setLabel('left',"| f(t) |",    **{'font-size': '12pt', 'color': 'k'})
        self.plotWidget_norm.setBackground("#FFFFFF00")
        self.plotWidget_norm.hideButtons()

        vbs = self.plotWidget_sin.getViewBox()
        vbc = self.plotWidget_cos.getViewBox()
        vbn = self.plotWidget_norm.getViewBox()

        vbs.setLimits(xMin=0, xMax=8192)
        vbc.setLimits(xMin=0, xMax=8192)
        vbn.setLimits(xMin=0, xMax=8192)
        vbs.setRange(xRange=(0, 8192/2), yRange=(-1, 1))
        vbc.setRange(xRange=(0, 8192/2), yRange=(-1, 1))
        vbn.setRange(xRange=(0, 8192/2), yRange=(-1, 1))
        vbs.setMouseEnabled(y=False,x=True)
        vbc.setMouseEnabled(y=False,x=True)
        vbn.setMouseEnabled(y=False,x=True)
        vbs.setMenuEnabled(False)
        vbc.setMenuEnabled(False)
        vbn.setMenuEnabled(False)

        self.plotWidget_cos.setXLink(self.plotWidget_sin)
        self.plotWidget_norm.setXLink(self.plotWidget_sin)
        self.plotWidget_cos.setYLink(self.plotWidget_sin)
        self.plotWidget_norm.setYLink(self.plotWidget_sin)

        # --- 前回の設定の読み込み ---
        latest_folder = settings.value("paths/latest_folder")
        if latest_folder:
            self.load_files(settings.value("paths/latest_folder"))

        visible = settings.value("dockVisible",True,type=bool)
        self.dock.setVisible(visible)
        self.default_size = self.size()
        self.restoreGeometry(settings.value("geometry", b""))

        # 現在の日時を取得
        now= datetime.now()
        self.text_log.setPlainText(f"・{now.year}/{now.month}/{now.day} {now.hour}:{now.minute}:{now.second}")
        self.text_log.appendPlainText("フーリエ変換ver3.0 起動")






#-------------実行部分-------------------------------------------------------------------------------------------------------------------------------------------------------

    def select_folder(self):
        #入力フォルダー選択
        folder = QFileDialog.getExistingDirectory(self, "フォルダ選択")
        if folder:
            self.statusBar().showMessage(folder)
        if not folder:
            return

        self.list_import.clear()
        settings.setValue("paths/latest_folder",folder)
        self.load_files(folder)

    def DandD(self, paths):
        path = paths[0] #先頭だけ表示
        self.statusBar().showMessage(path)
        self.list_import.clear()
        settings.setValue("paths/latest_folder",path)
        self.load_files(path)

    def load_files(self, folder):
        self.path_text.setText(folder)
        self.statusBar().showMessage("読み込み中")
        # 直下のファイル
        files = os.listdir(folder)
        if len(files) != 0:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full):
                    if NMR.header_check(full) == True:
                        self.add_checked_item(name,full)
        else:
            self.statusBar().showMessage("ファイルが存在しません:"+folder)
            return None

        # 1階層下のファイル
        for name in os.listdir(folder):
            full = os.path.join(folder, name)
            if os.path.isdir(full):
                for sub in os.listdir(full):
                    sub_full = os.path.join(full, sub)
                    if os.path.isfile(sub_full):
                        if NMR.header_check(sub_full) == True:
                            self.add_checked_item(sub,sub_full)
        self.statusBar().showMessage("読み込み完了:"+folder)

    def add_checked_item(self, sub, fullpath):
        item = QListWidgetItem(sub)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setData(Qt.UserRole,fullpath)
        self.list_import.addItem(item)

    def all_select(self):
        any_checked = False
        for i in range(self.list_import.count()):
            if self.list_import.item(i).checkState() == Qt.Checked:
                any_checked = True
                break

        new_state = Qt.Unchecked if any_checked else Qt.Checked

        for i in range(self.list_import.count()):
            self.list_import.item(i).setCheckState(new_state)

    def next(self):
        row = self.list_import.currentRow()
        count = self.list_import.count()

        if count == 0:
            return

        if row < 0:
            # 未選択なら先頭
            next_row = 0
        else:
            # 最後なら 0 に戻す
            next_row = (row + 1) % count

        self.list_import.setCurrentRow(next_row)


    def before(self):
        row = self.list_import.currentRow()
        count = self.list_import.count()

        if count == 0:
            return

        if row < 0:
            # 未選択なら先頭
            next_row = 0
        else:
            # 最後なら 0 に戻す
            next_row = (row - 1) % count

        self.list_import.setCurrentRow(next_row)

    def filename_clicked(self, item):
        clicked_path = item.data(Qt.UserRole)
        #データの読み込み
        raw_data = NMR.import_rawdata(clicked_path)

        #データをリストに表示
        tree = self.list_data
        tree.clear()

        parent = QTreeWidgetItem(tree,["メインの情報"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for name,data in raw_data.main().items():
            child_name = QTreeWidgetItem(parent, [name])
            child_data = QTreeWidgetItem(parent, [str(data)])
            child_name.setSizeHint(0, QSize(0, 18))
            child_data.setSizeHint(0, QSize(0, 18))
        parent.setExpanded(True)

        parent = QTreeWidgetItem(tree,["meta情報"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for name,data in raw_data.meta().items():
            child_name = QTreeWidgetItem(parent, [name])
            child_data = QTreeWidgetItem(parent, [data])
            child_name.setSizeHint(0, QSize(0, 18))
            child_data.setSizeHint(0, QSize(0, 18))
        parent.setExpanded(True)

        parent = QTreeWidgetItem(tree,["モジュレーター情報"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for name,data in raw_data.modulator().items():
            child_name = QTreeWidgetItem(parent, [name])
            child_data = QTreeWidgetItem(parent, [str(data)])
            child_name.setSizeHint(0, QSize(0, 18))
            child_data.setSizeHint(0, QSize(0, 18))

        parent = QTreeWidgetItem(tree,["T1T2info"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for name,data in raw_data.T1T2info().items():
            child_name = QTreeWidgetItem(parent, [name])
            child_data = QTreeWidgetItem(parent, [str(data)])
            child_name.setSizeHint(0, QSize(0, 18))
            child_data.setSizeHint(0, QSize(0, 18))

        parent = QTreeWidgetItem(tree,["others"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for name,data in raw_data.others().items():
            child_name = QTreeWidgetItem(parent, [name])
            child_data = QTreeWidgetItem(parent, [str(data)])
            child_name.setSizeHint(0, QSize(0, 18))
            child_data.setSizeHint(0, QSize(0, 18))

        parent = QTreeWidgetItem(tree,["variable"])

        # 太字
        font = parent.font(0)
        font.setBold(True)
        parent.setFont(0, font)

        # 高さ（行間を少し広く）
        parent.setSizeHint(0, QSize(0, 28))
        for data in raw_data.var():
            child_data = QTreeWidgetItem(parent, [str(data)])
            child_data.setSizeHint(0, QSize(0, 18))


        # --- グラフ設定 ---

        self.plotWidget_sin.clear()
        self.plotWidget_cos.clear()
        self.plotWidget_norm.clear()

        self.xs = np.arange(raw_data.wavesize)
        self.ys = raw_data.normalize_sin()
        self.yc = raw_data.normalize_cos()
        self.yp = np.sqrt(self.ys**2+self.yc**2)

        self.plotWidget_sin.plot(self.xs, self.ys, pen='k')
        self.plotWidget_cos.plot(self.xs, self.yc, pen='k')
        self.plotWidget_norm.plot(self.xs, self.yp, pen='k')

        self.plotWidget_sin.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget_cos.showGrid(x=True, y=True, alpha=0.3)
        self.plotWidget_norm.showGrid(x=True, y=True, alpha=0.3)




        # --- 縦ライン ---
        self.vline_sin = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.vline_cos = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.vline_norm = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.plotWidget_sin.addItem(self.vline_sin)
        self.plotWidget_cos.addItem(self.vline_cos)
        self.plotWidget_norm.addItem(self.vline_norm)
        self.vline_sin.hide()
        self.vline_cos.hide()
        self.vline_norm.hide()


    def onClick(self, event):
        pos = event.scenePos()

        if self.plotWidget_sin.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plotWidget_sin.plotItem.vb.mapSceneToView(pos)
            click_x = mouse_point.x()

            # 最近傍点の探索
            idx = np.abs(self.xs - click_x).argmin()
            nearest_x = self.xs[idx]
            nearest_y = self.ys[idx]

            # 縦ライン移動
            self.vline_sin.setValue(nearest_x)
            self.vline_sin.show()
            self.vline_cos.setValue(nearest_x)
            self.vline_cos.show()
            self.vline_norm.setValue(nearest_x)
            self.vline_norm.show()

            self.statusBar().showMessage(f"clicked \"sin\" at x={nearest_x}, y={nearest_y:.4f}")

        elif self.plotWidget_cos.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plotWidget_cos.plotItem.vb.mapSceneToView(pos)
            click_x = mouse_point.x()

            # 最近傍点の探索
            idx = np.abs(self.xs - click_x).argmin()
            nearest_x = self.xs[idx]
            nearest_y = self.yc[idx]

            # 縦ライン移動
            self.vline_sin.setValue(nearest_x)
            self.vline_sin.show()
            self.vline_cos.setValue(nearest_x)
            self.vline_cos.show()
            self.vline_norm.setValue(nearest_x)
            self.vline_norm.show()

            self.statusBar().showMessage(f"clicked \"cos\" at x={nearest_x}, y={nearest_y:.4f}")

        elif self.plotWidget_norm.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plotWidget_norm.plotItem.vb.mapSceneToView(pos)
            click_x = mouse_point.x()

            # 最近傍点の探索
            idx = np.abs(self.xs - click_x).argmin()
            nearest_x = self.xs[idx]
            nearest_y = self.yp[idx]

            # 縦ライン移動
            self.vline_sin.setValue(nearest_x)
            self.vline_sin.show()
            self.vline_cos.setValue(nearest_x)
            self.vline_cos.show()
            self.vline_norm.setValue(nearest_x)
            self.vline_norm.show()

            self.statusBar().showMessage(f"clicked \"norm\" at x={nearest_x}, y={nearest_y:.4f}")

    def quit_event(self,event):
        self.dock.hide()
        QApplication.quit()

    def closeEvent(self, event):
        settings.setValue("dockVisible",self.dockWidget.isVisible()) #終了時にログの表示/非表示を保存
        settings.setValue("geometry",self.saveGeometry())
        super().closeEvent(event)



#---------------------------------- メニューバー -----------------------------------------------------------

    def open_github(self):
        url = QUrl("https://github.com/E-Kraft/Unagi-project-FFT-Software-for-Itou-Lab.-")
        QDesktopServices.openUrl(url)

    def show_version_dialog(self):
        dialog = VersionDialog(self)
        dialog.exec()

    def show_thisapp_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def resize_default(self):
        self.setWindowState(Qt.WindowNoState)
        self.resize(self.default_size)
        screen = self.screen()
        screen_geometry = screen.availableGeometry()

        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())  # 任意のデフォルト位置




#--------------------------------------------------------- メインの実行部 --------------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    #qInstallMessageHandler(qt_message_handler)
    apply_stylesheet(app, theme='light_blue.xml',)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
