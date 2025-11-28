# mixin_io_plot.py
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from pyqtgraph.exporters import ImageExporter

class IOPlotMixin:
    """
    - 상태표시/FS설정
    - 데이터 로드(dummy/MAT/CSV)
    - 플롯 갱신
    - PNG 저장
    이 Mixin은 다음 속성들이 self에 있다고 가정:
      loader, analyzer, spin_fs, plot_ppg, plot_ecg, label_status
      t, ppg, ecg
    """

    # ----- 상태/FS -----
    def _update_status(self, msg: str):
        self.label_status.setText(msg)
        self.label_status.repaint()

    def _set_fs(self, fs: float):
        self.spin_fs.setValue(fs)
        self.loader.sampling_rate = fs
        self.analyzer.set_sampling_rate(fs)

    # ----- 플롯 -----
    def _plot_all(self):
        if self.t is None:
            return
        self.plot_ppg.plot_data(self.t, self.ppg)
        self.plot_ecg.plot_data(self.t, self.ecg)
        self.plot_ppg.clear_peaks()
        self.plot_ecg.clear_peaks()

    # ----- 로더 -----
    def load_mat(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select MAT file", "", "MAT files (*.mat)")
        if not path:
            return
        try:
            t, ppg, ecg, fs = self.loader.load_mat(path)
            self.t, self.ppg, self.ecg = t, ppg, ecg
            self._set_fs(fs)
            self._plot_all()
            self._update_status(f"MAT 로드 완료 | fs={fs:.2f} Hz | N={len(t)}")
        except Exception as e:
            QMessageBox.critical(self, "로드 실패", str(e))

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV files (*.csv)")
        if not path:
            return
        try:
            t, ppg, ecg, fs = self.loader.load_csv(path)
            self.t, self.ppg, self.ecg = t, ppg, ecg
            self._set_fs(fs)
            self._plot_all()
            self._update_status(f"CSV 로드 완료 | fs≈{fs:.2f} Hz | N={len(t)}")
        except Exception as e:
            QMessageBox.critical(self, "로드 실패", str(e))

    def load_dummy(self):
        t, ppg, ecg, fs = self.loader.generate_dummy(duration=15, fs=self.spin_fs.value())
        self.t, self.ppg, self.ecg = t, ppg, ecg
        self._set_fs(fs)
        self._plot_all()
        self._update_status(f"더미 데이터 로드 완료 | fs={fs:.2f} Hz | N={len(t)}")

    # ----- PNG 저장 -----
    def save_plots_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Plots PNG", "plots.png", "PNG Image (*.png)")
        if not path:
            return

        QApplication.processEvents()
        exporter1 = ImageExporter(self.plot_ppg.plotItem)
        exporter2 = ImageExporter(self.plot_ecg.plotItem)
        try:
            exporter1.export(path.replace(".png", "_ppg.png"))
            exporter2.export(path.replace(".png", "_ecg.png"))
            self._update_status(f"플롯 저장 완료: {path.replace('.png', '_ppg.png')}, {path.replace('.png', '_ecg.png')}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))
