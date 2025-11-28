# main_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QDoubleSpinBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from data_loader import DataLoader
from sync_analyzer import SyncAnalyzer
from graph_widget import GraphWidget

from mixin_roi_sync import ROISyncMixin
from mixin_io_plot import IOPlotMixin
from mixin_analyze_export import AnalyzeExportMixin


class ROISyncApp(QWidget, ROISyncMixin, IOPlotMixin, AnalyzeExportMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPG·ECG ROI 동기화 분석")
        self.resize(1000, 720)

        # data/logic
        self.loader = DataLoader()
        self.analyzer = SyncAnalyzer(self.loader.sampling_rate)

        # ---------- UI ----------
        root = QVBoxLayout(self)

        # Status
        self.label_status = QLabel("데이터 대기 중...")
        root.addWidget(self.label_status)

        # Controls
        ctrl = QHBoxLayout()

        self.btn_load_mat = QPushButton("Load MAT")
        self.btn_load_csv = QPushButton("Load CSV")
        self.btn_load_dummy = QPushButton("Load Dummy")

        ctrl.addWidget(self.btn_load_mat)
        ctrl.addWidget(self.btn_load_csv)
        ctrl.addWidget(self.btn_load_dummy)

        ctrl.addWidget(QLabel("Fs(Hz):"))
        self.spin_fs = QDoubleSpinBox()
        self.spin_fs.setRange(10, 2000)
        self.spin_fs.setDecimals(2)
        self.spin_fs.setValue(128.0)
        ctrl.addWidget(self.spin_fs)

        ctrl.addWidget(QLabel("Filter:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["default", "ppg_only", "off"])
        ctrl.addWidget(self.combo_filter)

        self.chk_detrend = QCheckBox("Detrend")
        self.chk_detrend.setChecked(True)
        ctrl.addWidget(self.chk_detrend)

        self.btn_analyze = QPushButton("Analyze ROI (HR/PTT/Delay)")
        ctrl.addWidget(self.btn_analyze)

        self.btn_export_csv = QPushButton("Export ROI CSV")
        ctrl.addWidget(self.btn_export_csv)

        self.btn_save_img = QPushButton("Save Plots PNG")
        ctrl.addWidget(self.btn_save_img)

        ctrl.addStretch(1)
        root.addLayout(ctrl)

        # Plots
        self.plot_ppg = GraphWidget("PPG Signal", color="g")
        self.plot_ecg = GraphWidget("ECG Signal", color="c")
        root.addWidget(self.plot_ppg, 1)
        root.addWidget(self.plot_ecg, 1)

        # ROI/X-range 동기화 설정 (mixin)
        self._init_roi_sync()

        # Connections
        self.btn_load_mat.clicked.connect(self.load_mat)
        self.btn_load_csv.clicked.connect(self.load_csv)
        self.btn_load_dummy.clicked.connect(self.load_dummy)
        self.btn_analyze.clicked.connect(self.analyze_roi)
        self.btn_export_csv.clicked.connect(self.export_roi_csv)
        self.btn_save_img.clicked.connect(self.save_plots_png)

        # data holders
        self.t = None
        self.ppg = None
        self.ecg = None
