# graph_widget.py
import pyqtgraph as pg
from typing import Optional, Iterable

class GraphWidget(pg.PlotWidget):
    def __init__(self, title="Signal", color="w"):
        super().__init__(title=title)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setBackground('k')
        self.curve = self.plot(pen=color)
        self.region: Optional[pg.LinearRegionItem] = None
        self.cross_v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#777'))
        self.addItem(self.cross_v, ignoreBounds=True)
        self.scatter: Optional[pg.ScatterPlotItem] = None

        # 성능 향상
        self.getPlotItem().setDownsampling(mode='peak')
        self.getPlotItem().setClipToView(True)

        # 마우스 이동 십자선
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def plot_data(self, x, y):
        self.curve.setData(x, y)

    def add_roi_region(self, start=2, end=4, on_change=None):
        """ROI 선택 영역 추가. on_change: 콜백(region.getRegion())"""
        if self.region is not None:
            self.removeItem(self.region)
        self.region = pg.LinearRegionItem([start, end], movable=True)
        self.region.setZValue(10)
        self.addItem(self.region)
        if on_change:
            self.region.sigRegionChanged.connect(lambda: on_change(self.region.getRegion()))
        return self.region

    def set_shared_region(self, region: pg.LinearRegionItem):
        """다른 위젯의 region을 공유(동일 객체 추가)"""
        if self.region is not None and self.region is not region:
            self.removeItem(self.region)
        self.region = region
        self.addItem(self.region)

    def get_roi_range(self):
        if self.region:
            return self.region.getRegion()
        return None

    def show_peaks(self, x_vals: Iterable[float], y_vals: Iterable[float]):
        """피크 마커 표시"""
        if self.scatter:
            self.removeItem(self.scatter)
        self.scatter = pg.ScatterPlotItem(x=list(x_vals), y=list(y_vals), size=6)
        self.addItem(self.scatter)

    def clear_peaks(self):
        if self.scatter:
            self.removeItem(self.scatter)
            self.scatter = None

    def _on_mouse_moved(self, pos):
        vb = self.getViewBox()
        if vb is None:
            return
        if self.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            self.cross_v.setPos(mouse_point.x())
