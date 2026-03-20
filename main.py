import sys
import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

STYLESHEET = """
* {
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
}
#card {
    background: #1a1b26;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}
#title {
    color: #565f89;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QPushButton#btnMin,
QPushButton#btnClose {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #565f89;
    font-size: 14px;
}
QPushButton#btnMin:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #a9b1d6;
}
QPushButton#btnClose:hover {
    background: #f7768e;
    color: #1a1b26;
}
QLabel#section {
    color: #565f89;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.8px;
}
QLineEdit {
    background: #16161e;
    border: 1.5px solid #292e42;
    border-radius: 8px;
    padding: 8px 10px;
    color: #c0caf5;
    font-size: 13px;
    selection-background-color: #3d59a1;
}
QLineEdit:focus {
    border-color: #7aa2f7;
}
QLineEdit:disabled {
    background: #13131a;
    color: #3b4261;
    border-color: #1e1f2e;
}
QPushButton#btnLock {
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 14px;
}
QPushButton#btnLock:hover {
    background: rgba(255, 255, 255, 0.05);
}
QLabel#aimLabel {
    color: #7aa2f7;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.8px;
}
QLabel#aimValue {
    color: #c0caf5;
    font-size: 22px;
    font-weight: 300;
}
QLabel#aimWarn {
    color: #f7768e;
    font-size: 22px;
    font-weight: 300;
}
"""


class CalcWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Artillery")
        self._locked = False
        self._drag = None
        self._build_ui()
        g = QApplication.primaryScreen().availableGeometry()
        self.move(g.center() - self.rect().center())

    def _build_ui(self):
        self.setFixedSize(340, 310)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        card = QWidget()
        card.setObjectName("card")
        fx = QGraphicsDropShadowEffect()
        fx.setBlurRadius(30)
        fx.setOffset(0, 6)
        fx.setColor(QColor(0, 0, 0, 100))
        card.setGraphicsEffect(fx)
        root.addWidget(card)

        col = QVBoxLayout(card)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        #title bar
        bar = QWidget()
        bar.setFixedHeight(42)
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(18, 0, 8, 0)
        bh.setSpacing(2)
        lbl = QLabel("Artillery")
        lbl.setObjectName("title")
        bh.addWidget(lbl)
        bh.addStretch()
        for txt, fn, oid in [("─", self.showMinimized, "btnMin"),
                              ("✕", self.close, "btnClose")]:
            b = QPushButton(txt)
            b.setObjectName(oid)
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            bh.addWidget(b)
        col.addWidget(bar)

        #body
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(18, 0, 18, 18)
        bl.setSpacing(12)

        # target header
        th = QHBoxLayout()
        s1 = QLabel("TARGET")
        s1.setObjectName("section")
        th.addWidget(s1)
        th.addStretch()
        self.btnLock = QPushButton("\U0001F513")
        self.btnLock.setObjectName("btnLock")
        self.btnLock.setFixedSize(28, 28)
        self.btnLock.setCursor(Qt.PointingHandCursor)
        self.btnLock.clicked.connect(self._toggle_lock)
        th.addWidget(self.btnLock)
        bl.addLayout(th)

        # target inputs
        tr = QHBoxLayout()
        tr.setSpacing(8)
        self.tD = self._inp("Dist (m)")
        self.tA = self._inp("Az (°)")
        tr.addWidget(self.tD)
        tr.addWidget(self.tA)
        bl.addLayout(tr)

        # offset header
        s2 = QLabel("OFFSET")
        s2.setObjectName("section")
        bl.addWidget(s2)

        # offset inputs
        orw = QHBoxLayout()
        orw.setSpacing(8)
        self.oD = self._inp("Dist (m)")
        self.oA = self._inp("Az (°)")
        orw.addWidget(self.oD)
        orw.addWidget(self.oA)
        bl.addLayout(orw)

        # separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#292e42;")
        bl.addWidget(sep)

        # result
        al = QLabel("AIM AT")
        al.setObjectName("aimLabel")
        bl.addWidget(al)
        ar = QHBoxLayout()
        ar.setSpacing(20)
        self.rD = QLabel("—")
        self.rD.setObjectName("aimValue")
        self.rA = QLabel("—")
        self.rA.setObjectName("aimValue")
        ar.addWidget(self.rD)
        ar.addWidget(self.rA)
        bl.addLayout(ar)

        col.addWidget(body)
        self.setStyleSheet(STYLESHEET)

        for w in (self.tD, self.tA, self.oD, self.oA):
            w.textChanged.connect(self._calc)
        self.tD.returnPressed.connect(lambda: self.tA.setFocus())
        self.tA.returnPressed.connect(lambda: self.oD.setFocus())
        self.oD.returnPressed.connect(lambda: self.oA.setFocus())

    @staticmethod
    def _inp(ph):
        e = QLineEdit()
        e.setPlaceholderText(ph)
        e.setAlignment(Qt.AlignCenter)
        e.setFixedHeight(36)
        return e

    #lock
    def _toggle_lock(self):
        self._locked = not self._locked
        self.btnLock.setText("\U0001F512" if self._locked else "\U0001F513")
        self.tD.setEnabled(not self._locked)
        self.tA.setEnabled(not self._locked)

    # ── calculation ──
    @staticmethod
    def _f(text):
        try:
            return float(text.strip().replace(",", "."))
        except ValueError:
            return None

    def _calc(self):
        vals = [self._f(w.text()) for w in (self.tD, self.tA, self.oD, self.oA)]
        dash = "—"
        if None in vals:
            self.rD.setText(dash)
            self.rA.setText(dash)
            return
        td, ta, od, oa = vals
        if td < 40 or not 0 <= ta <= 360 or od < 0 or not 0 <= oa <= 360:
            self.rD.setText(dash)
            self.rA.setText(dash)
            return

        ar = math.radians(ta % 360)
        br = math.radians(oa % 360)
        xc = td * math.sin(ar) - od * math.sin(br)
        yc = td * math.cos(ar) - od * math.cos(br)

        dist = round(math.hypot(xc, yc) * 2) / 2
        azim = round(math.degrees(math.atan2(xc, yc)) % 360 * 10) / 10

        self.rD.setObjectName("aimWarn" if dist < 40 else "aimValue")
        self.rD.setStyleSheet(self.rD.styleSheet())          # refresh
        self.rD.setText(f"{dist:.1f} m")
        self.rA.setObjectName("aimValue")
        self.rA.setText(f"{azim:.1f}°")

    #drag
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.pos().y() <= 52:
            self._drag = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag:
            self.move(e.globalPos() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    win = CalcWindow()
    win.show()
    sys.exit(app.exec_())
