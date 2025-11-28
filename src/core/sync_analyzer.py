# sync_analyzer.py
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict, Optional
from scipy.signal import butter, filtfilt, find_peaks, resample_poly, detrend as sp_detrend

@dataclass
class ROIResult:
    start_s: float
    end_s: float
    n_samples: int
    fs: float
    hr_bpm: Optional[float]
    rr_mean_s: Optional[float]
    rr_sd_s: Optional[float]
    ptt_mean_s: Optional[float]
    ptt_sd_s: Optional[float]
    delay_xcorr_s: Optional[float]
    sqi: Dict[str, float]

class SyncAnalyzer:
    def __init__(self, sampling_rate: float = 128.0):
        self.sampling_rate = sampling_rate
        self.roi_start = None
        self.roi_end = None

    # ----------------- config -----------------
    def set_sampling_rate(self, fs: float):
        self.sampling_rate = float(fs)

    def set_roi(self, start_time: float, end_time: float):
        if end_time <= start_time:
            raise ValueError("ROI 종료시간이 시작시간보다 커야 합니다.")
        self.roi_start = start_time
        self.roi_end = end_time

    # ----------------- basic utils -----------------
    def extract_roi(self, signal: np.ndarray) -> np.ndarray:
        if self.roi_start is None or self.roi_end is None:
            raise ValueError("ROI가 설정되지 않았습니다.")
        start_idx = int(self.roi_start * self.sampling_rate)
        end_idx = int(self.roi_end * self.sampling_rate)
        start_idx = max(0, start_idx)
        end_idx = min(len(signal), end_idx)
        return signal[start_idx:end_idx]

    def align_signals(self, ppg: np.ndarray, ecg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        min_len = min(len(ppg), len(ecg))
        return ppg[:min_len], ecg[:min_len]

    # ----------------- filters -----------------
    def bandpass(self, x: np.ndarray, low: float, high: float, order: int = 4) -> np.ndarray:
        nyq = 0.5 * self.sampling_rate
        lowc = low / nyq
        highc = high / nyq
        b, a = butter(order, [lowc, highc], btype="band")
        return filtfilt(b, a, x)

    def detrend(self, x: np.ndarray) -> np.ndarray:
        return sp_detrend(x)

    def zscore(self, x: np.ndarray) -> np.ndarray:
        s = np.std(x)
        return (x - np.mean(x)) / (s if s > 1e-12 else 1.0)

    def resample_to(self, x: np.ndarray, orig_fs: float, target_fs: float) -> Tuple[np.ndarray, float]:
        if abs(orig_fs - target_fs) < 1e-6:
            return x, orig_fs
        # rational resampling
        from math import gcd
        up = int(round(target_fs))
        down = int(round(orig_fs))
        g = gcd(up, down)
        up //= g; down //= g
        y = resample_poly(x, up, down)
        return y, target_fs

    # ----------------- peaks & metrics -----------------
    def detect_ecg_rpeaks(self, ecg_f: np.ndarray) -> np.ndarray:
        # 간단: z-score + peak prominence
        z = self.zscore(ecg_f)
        peaks, _ = find_peaks(z, distance=int(0.25*self.sampling_rate), prominence=1.0)
        return peaks

    def detect_ppg_peaks(self, ppg_f: np.ndarray) -> np.ndarray:
        z = self.zscore(ppg_f)
        peaks, _ = find_peaks(z, distance=int(0.3*self.sampling_rate), prominence=0.3)
        return peaks

    def compute_hr(self, peak_indices: np.ndarray) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if len(peak_indices) < 2:
            return None, None, None
        rr = np.diff(peak_indices) / self.sampling_rate
        hr = 60.0 / np.mean(rr) if np.mean(rr) > 0 else None
        return hr, float(np.mean(rr)), float(np.std(rr))

    def map_ptt(self, r_idx: np.ndarray, ppg_idx: np.ndarray) -> np.ndarray:
        # ECG R-peak 이후에 가장 가까운 PPG peak와 매칭
        if len(r_idx) == 0 or len(ppg_idx) == 0:
            return np.array([])
        ptts = []
        j = 0
        for r in r_idx:
            while j < len(ppg_idx) and ppg_idx[j] < r:
                j += 1
            if j < len(ppg_idx):
                ptt_s = (ppg_idx[j] - r) / self.sampling_rate
                if 0.0 < ptt_s < 1.5:  # 합리적 범위
                    ptts.append(ptt_s)
        return np.array(ptts)

    def delay_by_xcorr(self, x: np.ndarray, y: np.ndarray) -> float:
        # y가 x 대비 얼마나 뒤로(+) 밀려 있는지 추정 (샘플 단위)
        x0 = self.zscore(x)
        y0 = self.zscore(y)
        corr = np.correlate(y0, x0, mode='full')
        lag = np.argmax(corr) - (len(x0) - 1)
        return lag / self.sampling_rate

    # ----------------- SQI -----------------
    def compute_sqi(self, x: np.ndarray) -> Dict[str, float]:
        # 매우 간단한 SQI: 포화율, 플랫율, SNR-ish
        x = np.asarray(x)
        rng = np.max(x) - np.min(x) + 1e-9
        sat = np.mean((x > (np.max(x) - 0.01*rng)) | (x < (np.min(x) + 0.01*rng)))
        flat = np.mean(np.abs(np.diff(x)) < 1e-4)
        snr_like = (np.var(x) / (np.mean(np.abs(np.diff(x))) + 1e-9))
        return {"saturation": float(sat), "flatness": float(flat), "snr_like": float(snr_like)}

    # ----------------- end-to-end ROI analysis -----------------
    def analyze_roi(
        self,
        t: np.ndarray,
        ppg: np.ndarray,
        ecg: np.ndarray,
        do_detrend: bool = True,
        filt_mode: str = "default"
    ) -> ROIResult:
        if self.roi_start is None or self.roi_end is None:
            raise ValueError("ROI가 설정되지 않았습니다.")

        # 1) ROI 추출
        ppg_roi = self.extract_roi(ppg)
        ecg_roi = self.extract_roi(ecg)
        t_roi = self.extract_roi(t)

        # 2) 전처리
        if do_detrend:
            ppg_roi = self.detrend(ppg_roi)
            ecg_roi = self.detrend(ecg_roi)

        if filt_mode == "default" or filt_mode == "ppg_ecg":
            # ECG: 5~15 Hz (아주 간단)
            ecg_f = self.bandpass(ecg_roi, 5.0, 15.0)
            # PPG: 0.5~5 Hz
            ppg_f = self.bandpass(ppg_roi, 0.5, 5.0)
        elif filt_mode == "ppg_only":
            ecg_f = ecg_roi
            ppg_f = self.bandpass(ppg_roi, 0.5, 5.0)
        elif filt_mode == "off":
            ecg_f = ecg_roi
            ppg_f = ppg_roi
        else:
            ecg_f = ecg_roi
            ppg_f = ppg_roi

        # 3) 피크 탐지/지표
        r_idx = self.detect_ecg_rpeaks(ecg_f)
        ppg_pk = self.detect_ppg_peaks(ppg_f)

        hr_bpm, rr_mean_s, rr_sd_s = self.compute_hr(r_idx)
        ptt_arr = self.map_ptt(r_idx, ppg_pk)
        ptt_mean_s = float(np.mean(ptt_arr)) if len(ptt_arr) else None
        ptt_sd_s = float(np.std(ptt_arr)) if len(ptt_arr) else None

        # 4) 교차상관 기반 지연 추정
        ppg_cut, ecg_cut = self.align_signals(ppg_f, ecg_f)
        delay_s = self.delay_by_xcorr(ecg_cut, ppg_cut)  # +면 PPG가 뒤

        # 5) SQI
        sqi = self.compute_sqi(ppg_f)

        return ROIResult(
            start_s=self.roi_start,
            end_s=self.roi_end,
            n_samples=len(t_roi),
            fs=self.sampling_rate,
            hr_bpm=(float(hr_bpm) if hr_bpm is not None else None),
            rr_mean_s=rr_mean_s,
            rr_sd_s=rr_sd_s,
            ptt_mean_s=ptt_mean_s,
            ptt_sd_s=ptt_sd_s,
            delay_xcorr_s=float(delay_s),
            sqi=sqi
        )
