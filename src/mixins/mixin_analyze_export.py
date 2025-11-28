# mixin_analyze_export.py
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox
from scipy.signal import find_peaks

class AnalyzeExportMixin:
    """
    - ROI 분석(HR/PTT/Delay)
    - ROI CSV 내보내기
    이 Mixin은 다음 속성들이 self에 있다고 가정:
      analyzer, t, ppg, ecg, spin_fs, combo_filter, chk_detrend,
      plot_ppg, plot_ecg, _update_status(), get_current_roi()
    """

    def analyze_roi(self):
        if any(getattr(self, k) is None for k in ["t", "ppg", "ecg"]):
            QMessageBox.warning(self, "안내", "데이터를 먼저 로드하세요.")
            return

        roi = self.get_current_roi()
        if not roi:
            QMessageBox.warning(self, "안내", "ROI를 선택하세요.")
            return
        start, end = roi
        self.analyzer.set_sampling_rate(self.spin_fs.value())
        self.analyzer.set_roi(start, end)

        filt_mode = self.combo_filter.currentText()
        do_detrend = self.chk_detrend.isChecked()

        try:
            res = self.analyzer.analyze_roi(self.t, self.ppg, self.ecg, do_detrend=do_detrend, filt_mode=filt_mode)
        except Exception as e:
            QMessageBox.critical(self, "분석 실패", str(e))
            return

        # ROI 피크 표시 (표시용 간단 탐지)
        fs = res.fs
        s_idx = int(res.start_s * fs)
        e_idx = int(res.end_s * fs)
        t_roi = self.t[s_idx:e_idx]
        ppg_roi = self.ppg[s_idx:e_idx]
        ecg_roi = self.ecg[s_idx:e_idx]

        p_pg, _ = find_peaks(ppg_roi, distance=int(0.3 * fs))
        p_ecg, _ = find_peaks(ecg_roi, distance=int(0.25 * fs))
        self.plot_ppg.show_peaks(t_roi[p_pg], ppg_roi[p_pg])
        self.plot_ecg.show_peaks(t_roi[p_ecg], ecg_roi[p_ecg])

        txt = [
            f"ROI {res.start_s:.2f}~{res.end_s:.2f}s | N={res.n_samples} | fs={res.fs:.2f}Hz",
            f"HR = {res.hr_bpm:.1f} bpm" if res.hr_bpm is not None else "HR = n/a",
            f"RR mean = {res.rr_mean_s:.3f}s (SD={res.rr_sd_s:.3f}s)" if res.rr_mean_s is not None else "RR = n/a",
            f"PTT mean = {res.ptt_mean_s:.3f}s (SD={res.ptt_sd_s:.3f}s)" if res.ptt_mean_s is not None else "PTT = n/a",
            f"Delay(xcorr) = {res.delay_xcorr_s:.4f}s",
            f"SQI: sat={res.sqi['saturation']:.3f}, flat={res.sqi['flatness']:.3f}, snr_like={res.sqi['snr_like']:.3f}",
        ]
        self._update_status(" | ".join(txt))

    def export_roi_csv(self):
        if any(getattr(self, k) is None for k in ["t", "ppg", "ecg"]):
            QMessageBox.warning(self, "안내", "데이터를 먼저 로드하세요.")
            return

        roi = self.get_current_roi()
        if not roi:
            QMessageBox.warning(self, "안내", "ROI를 선택하세요.")
            return

        start, end = roi
        fs = self.spin_fs.value()
        s_idx = int(start * fs)
        e_idx = int(end * fs)
        s_idx = max(0, s_idx)
        e_idx = min(len(self.t), e_idx)

        if e_idx - s_idx < 2:
            QMessageBox.warning(self, "안내", "ROI 길이가 너무 짧습니다.")
            return

        df = pd.DataFrame({
            "time": self.t[s_idx:e_idx],
            "ppg": self.ppg[s_idx:e_idx],
            "ecg": self.ecg[s_idx:e_idx],
        })

        path, _ = QFileDialog.getSaveFileName(self, "Export ROI CSV", "roi_segment.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            df.to_csv(path, index=False)
            self._update_status(f"ROI CSV 저장 완료: {path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", str(e))
