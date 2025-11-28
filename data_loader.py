# data_loader.py
import numpy as np
import pandas as pd
from scipy.io import loadmat
from typing import Optional, Tuple, Dict, Any

class DataLoader:
    """
    - MAT: ppg/ecg 키 자동 탐색, fs(또는 sampling_rate) 자동 인식
    - CSV: 열 이름 자동 추정(ppg, ecg, time/fs), 샘플링레이트 추정
    - API:
        load_mat(path, ppg_key?, ecg_key?, fs_key?) -> (t, ppg, ecg, fs)
        load_csv(path, time_col?, ppg_col?, ecg_col?, fs?) -> (t, ppg, ecg, fs)
        generate_dummy(duration=10, fs=128)
    """
    def __init__(self, default_fs: float = 128.0):
        self.ppg: Optional[np.ndarray] = None
        self.ecg: Optional[np.ndarray] = None
        self.t: Optional[np.ndarray] = None
        self.sampling_rate: float = default_fs

    # ---------- helpers ----------
    @staticmethod
    def _flatten_if_needed(x: Any) -> np.ndarray:
        arr = np.array(x).astype(float).squeeze()
        return arr.ravel()

    @staticmethod
    def _find_first_key(d: Dict[str, Any], candidates) -> Optional[str]:
        for c in candidates:
            if c in d:
                return c
        # try case-insensitive
        lower_map = {k.lower(): k for k in d.keys()}
        for c in candidates:
            if c.lower() in lower_map:
                return lower_map[c.lower()]
        return None

    # ---------- MAT ----------
    def load_mat(
        self,
        mat_path: str,
        ppg_key: Optional[str] = None,
        ecg_key: Optional[str] = None,
        fs_key: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        try:
            mdict = loadmat(mat_path)
        except Exception as e:
            raise RuntimeError(f"MAT 파일 로드 실패: {e}")

        # remove meta keys
        data_keys = {k: v for k, v in mdict.items() if not k.startswith("__")}

        # find keys
        ppg_key = ppg_key or self._find_first_key(
            data_keys, ["ppg_raw", "ppg", "PPG", "ppgSignal", "ppg_signal"]
        )
        ecg_key = ecg_key or self._find_first_key(
            data_keys, ["ecg_raw", "ecg", "ECG", "ecgSignal", "ecg_signal"]
        )
        fs_key = fs_key or self._find_first_key(
            data_keys, ["fs", "FS", "sampling_rate", "Fs", "sample_rate"]
        )

        if ppg_key is None or ecg_key is None:
            raise RuntimeError(f"MAT 내부에 PPG/ECG 키를 찾지 못했습니다. 키 후보를 지정하세요. (keys={list(data_keys.keys())[:10]}...)")

        ppg = self._flatten_if_needed(data_keys[ppg_key])
        ecg = self._flatten_if_needed(data_keys[ecg_key])

        if fs_key is not None:
            fs_val = float(np.array(data_keys[fs_key]).squeeze())
            self.sampling_rate = fs_val
        else:
            # fallback 기존 기본값
            pass

        n = min(len(ppg), len(ecg))
        ppg, ecg = ppg[:n], ecg[:n]
        t = np.arange(n) / self.sampling_rate

        self.ppg, self.ecg, self.t = ppg, ecg, t
        return t, ppg, ecg, self.sampling_rate

    # ---------- CSV ----------
    def load_csv(
        self,
        csv_path: str,
        time_col: Optional[str] = None,
        ppg_col: Optional[str] = None,
        ecg_col: Optional[str] = None,
        fs: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise RuntimeError(f"CSV 파일 로드 실패: {e}")

        cols = [c.lower() for c in df.columns]
        colmap = {c.lower(): c for c in df.columns}

        # guess columns
        if time_col is None:
            for c in ["time", "t", "sec", "seconds", "ms", "timestamp"]:
                if c in cols:
                    time_col = colmap[c]; break

        if ppg_col is None:
            for c in ["ppg", "ppg_raw", "ppgsignal", "ppg_signal"]:
                if c in cols:
                    ppg_col = colmap[c]; break

        if ecg_col is None:
            for c in ["ecg", "ecg_raw", "ecgsignal", "ecg_signal"]:
                if c in cols:
                    ecg_col = colmap[c]; break

        if ppg_col is None or ecg_col is None:
            raise RuntimeError(f"CSV에서 PPG/ECG 열을 찾지 못했습니다. (columns={list(df.columns)})")

        ppg = df[ppg_col].to_numpy(dtype=float)
        ecg = df[ecg_col].to_numpy(dtype=float)
        n = min(len(ppg), len(ecg))
        ppg, ecg = ppg[:n], ecg[:n]

        if time_col is not None:
            t_raw = df[time_col].to_numpy(dtype=float)[:n]
            # infer fs
            if fs is None and len(t_raw) > 2:
                dt = np.median(np.diff(t_raw))
                if dt > 0:
                    fs = 1.0 / dt
        else:
            fs = fs or self.sampling_rate
            t_raw = np.arange(n) / fs

        self.sampling_rate = fs or self.sampling_rate
        self.ppg, self.ecg, self.t = ppg, ecg, t_raw
        return t_raw, ppg, ecg, self.sampling_rate

    # ---------- dummy ----------
    def generate_dummy(self, duration: int = 10, fs: Optional[float] = None):
        fs = fs or self.sampling_rate
        t = np.linspace(0, duration, int(duration * fs), endpoint=False)
        # 간단한 합성 파형
        ppg = 0.6*np.sin(2*np.pi*1.2*t) + 0.3*np.sin(2*np.pi*2.4*t) + 0.05*np.random.randn(len(t))
        # ECG는 위상차와 날카로운 R-peak 유사형
        ecg = 0.4*np.sin(2*np.pi*1.0*t + 0.4) + 0.6*(np.mod(t*1.0, 1) < 0.02).astype(float) + 0.05*np.random.randn(len(t))
        self.t, self.ppg, self.ecg = t, ppg, ecg
        self.sampling_rate = fs
        return t, ppg, ecg, fs
