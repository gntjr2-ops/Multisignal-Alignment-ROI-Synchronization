# mixin_roi_sync.py
from typing import Tuple

class ROISyncMixin:
    """
    - 두 Plot에 별도의 ROI 생성
    - ROI 상호 동기화 (무한루프 방지 락)
    - X축 동기화
    - 상태표시 헬퍼(_roi_changed)
    이 Mixin은 다음 속성들이 self에 있다고 가정:
      plot_ppg, plot_ecg : GraphWidget
      label_status       : QLabel
      t                  : np.ndarray | None
    """

    def _init_roi_sync(self):
        # ROI 생성 및 양방향 동기화
        self._region_sync_lock = False
        self.region_ppg = self.plot_ppg.add_roi_region(start=2, end=4, on_change=self._on_region_change_from_ppg)
        self.region_ecg = self.plot_ecg.add_roi_region(start=2, end=4, on_change=self._on_region_change_from_ecg)

        # X-range sync
        self.plot_ppg.sigXRangeChanged.connect(lambda: self.sync_graphs(self.plot_ppg, self.plot_ecg))
        self.plot_ecg.sigXRangeChanged.connect(lambda: self.sync_graphs(self.plot_ecg, self.plot_ppg))

    # ----- ROI 콜백 -----
    def _on_region_change_from_ppg(self, region: Tuple[float, float]):
        if self._region_sync_lock:
            return
        self._region_sync_lock = True
        try:
            if self.region_ecg is not None:
                self.region_ecg.setRegion(region)
            self._roi_changed(region)
        finally:
            self._region_sync_lock = False

    def _on_region_change_from_ecg(self, region: Tuple[float, float]):
        if self._region_sync_lock:
            return
        self._region_sync_lock = True
        try:
            if self.region_ppg is not None:
                self.region_ppg.setRegion(region)
            self._roi_changed(region)
        finally:
            self._region_sync_lock = False

    # ----- 공용 헬퍼 -----
    def _roi_changed(self, region: Tuple[float, float]):
        if getattr(self, "t", None) is None:
            return
        start, end = region
        self.label_status.setText(f"ROI {start:.2f}~{end:.2f}s")
        self.label_status.repaint()

    def sync_graphs(self, source, target):
        x_range = source.viewRange()[0]
        target.setXRange(x_range[0], x_range[1], padding=0)

    def get_current_roi(self):
        return self.region_ppg.getRegion() if getattr(self, "region_ppg", None) else None
