import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import loadUiType
import pyqtgraph as pg
from qt_material import apply_stylesheet
import NMR
from datetime import datetime




Ui_MainWindow, _ = loadUiType("graphui.ui")



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        #ステータスバーの設定
        self.statusBar().setStyleSheet("""
        QStatusBar{
        background-color: #f5f5f5;
        font-size: 14px;
        padding: 6px 8px;
        border-bottom: 1px solid #e0e0e0;
        }
        """)
        self.statusBar().showMessage("準備完了")

        # UIの PlotWidget（objectName="plot_widget"）
        self.plotWidget_sin = self.plot_widget_sin
        self.plotWidget_cos = self.plot_widget_cos
        self.plotWidget_pow = self.plot_widget_pow

        #UIの lebel
        #self.label_sin = self.label_widget_sin
        #self.label_sin.setScaledContents(True)
        #画像配置

        #log
        # 現在の日時を取得
        now= datetime.now()
        self.text_log = self.textBrowser_widget_log
        self.text_log.setPlainText(f"・{now.year}/{now.month}/{now.day} {now.hour}:{now.minute}:{now.second}")
        self.text_log.appendPlainText("フーリエ変換ver3.0 起動")

        # --- データ作成 ---
        #変数の定義
        zeropoint = 1400 #ゼロポイント
        n_ind= 3441 #切り取り範囲(負)
        p_ind = 4752 #切り取り範囲(正)
        base_angle = np.pi / 100 #基本の位相回転角(フーリエ変換ver2.5参照)　optionで選択できるようにするかも
        file_path = '10k0613T2F.1010'

        #-------------実行部分---------------------

        #データの読み込み
        raw_data = NMR.import_rawdata(file_path)

        self.xs = np.arange(raw_data.wavesize)
        self.ys = raw_data.normalize_sin()
        self.yc = raw_data.normalize_cos()
        self.yp = np.sqrt(self.ys**2+self.yc**2)


        # --- 表示 ---
        self.plotWidget_sin.plot(self.xs, self.ys, pen='k')
        self.plotWidget_sin.setTitle("<span style='color:black'>SIN</span>")
        self.plotWidget_sin.setBackground("#FFFFFF00")

        self.plotWidget_cos.plot(self.xs, self.yc, pen='k')
        self.plotWidget_cos.setTitle("<span style='color:black'>COS</span>")
        self.plotWidget_cos.setBackground("#FFFFFF00")

        self.plotWidget_pow.plot(self.xs, self.yp, pen='k')
        self.plotWidget_pow.setTitle("<span style='color:black'>S^2+c^2</span>")
        self.plotWidget_pow.setBackground("#FFFFFF00")

        vbs = self.plotWidget_sin.getViewBox()
        vbc = self.plotWidget_cos.getViewBox()
        vbp = self.plotWidget_pow.getViewBox()

        vbs.setLimits(xMin=0, xMax=raw_data.wavesize)
        vbc.setLimits(xMin=0, xMax=raw_data.wavesize)
        vbp.setLimits(xMin=0, xMax=raw_data.wavesize)
        vbs.setRange(xRange=(0,raw_data.wavesize/2), yRange=(-1, 1))
        vbc.setRange(xRange=(0, raw_data.wavesize/2), yRange=(-1, 1))
        vbp.setRange(xRange=(0, raw_data.wavesize/2), yRange=(-1, 1))
        vbs.setMouseEnabled(y=False,x=True)
        vbc.setMouseEnabled(y=False,x=True)
        vbp.setMouseEnabled(y=False,x=True)

        self.plotWidget_cos.setXLink(self.plotWidget_sin)
        self.plotWidget_pow.setXLink(self.plotWidget_sin)
        self.plotWidget_cos.setYLink(self.plotWidget_sin)
        self.plotWidget_pow.setYLink(self.plotWidget_sin)

        # --- 縦ライン ---
        self.vline_sin = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.vline_cos = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.vline_pow = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('r', width=2))
        self.plotWidget_sin.addItem(self.vline_sin)
        self.plotWidget_cos.addItem(self.vline_cos)
        self.plotWidget_pow.addItem(self.vline_pow)
        self.vline_sin.hide()
        self.vline_cos.hide()
        self.vline_pow.hide()

        # --- クリック検出 ---
        self.plotWidget_sin.scene().sigMouseClicked.connect(self.onClick)
        self.plotWidget_cos.scene().sigMouseClicked.connect(self.onClick)
        self.plotWidget_pow.scene().sigMouseClicked.connect(self.onClick)

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
            self.vline_pow.setValue(nearest_x)
            self.vline_pow.show()

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
            self.vline_pow.setValue(nearest_x)
            self.vline_pow.show()

            self.statusBar().showMessage(f"clicked \"cos\" at x={nearest_x}, y={nearest_y:.4f}")

        elif self.plotWidget_pow.plotItem.sceneBoundingRect().contains(pos):
            mouse_point = self.plotWidget_pow.plotItem.vb.mapSceneToView(pos)
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
            self.vline_pow.setValue(nearest_x)
            self.vline_pow.show()

            self.statusBar().showMessage(f"clicked \"pow\" at x={nearest_x}, y={nearest_y:.4f}")










if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_blue.xml',)
    #apply_stylesheet(app, theme='dark_blue.xml',)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
