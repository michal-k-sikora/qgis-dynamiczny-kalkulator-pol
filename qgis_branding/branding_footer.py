# -*- coding: utf-8 -*-
"""
Wspólna stopka OnGeo dla wtyczek QGIS.

"""

from typing import Iterable, List, Tuple, Optional
from qgis.PyQt.QtCore import Qt, QUrl, QRectF, QSize
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from qgis.PyQt import QtGui
from qgis.PyQt.QtSvg import QSvgRenderer
from . import resources_rc  # rejestruje :/branding/...

# ──────────────────────────────────────────────────────────────────────────────
# 🔧 DOMYŚLNE USTAWIENIA BRANDINGU ONGEO
DEFAULT_LOGO_PATH = ":/branding/icons/logo.svg"

# >>> ROZMIAR LOGO (proporcje zachowane) <<<
DEFAULT_MAX_LOGO_WIDTH  = 150    # np. 140 / 160 / 180
DEFAULT_MAX_LOGO_HEIGHT = None   # None => wylicz z proporcji; lub np. 44

# >>> TU ustawisz domyślny TEKST pod logo <<<
DEFAULT_SUBTITLE_TEXT = "© 2025 Michał Sikora | OnGeo sp. z o.o."
# ──────────────────────────────────────────────────────────────────────────────


def open_url(url: str):
    """Otwiera podany adres URL w domyślnej przeglądarce."""
    QtGui.QDesktopServices.openUrl(QUrl(url))


class LinkButton(QPushButton):
    """Płaski przycisk wyglądający jak hiperłącze."""
    def __init__(self, title: str, url: str, parent: Optional[QWidget] = None):
        super().__init__(title, parent)
        self._url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet("""
            QPushButton {
                color: palette(link);
                text-decoration: underline;
                background: transparent;
                border: none;
                padding: 2px 8px;
            }
            QPushButton:hover { color: palette(highlight); }
        """)
        self.clicked.connect(lambda: open_url(self._url))


class AspectRatioSvgWidget(QWidget):
    """
    Wektorowy widget do wyświetlania SVG z zachowaniem proporcji,
    renderowany bezpośrednio przez QSvgRenderer (ostry w każdej skali).
    """
    def __init__(self,
                 svg_path: str,
                 max_width: Optional[int] = DEFAULT_MAX_LOGO_WIDTH,
                 max_height: Optional[int] = DEFAULT_MAX_LOGO_HEIGHT,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("AspectRatioSvgWidget")
        self._renderer = QSvgRenderer(svg_path, self)
        # Proporcje na podstawie viewBox
        vb = self._renderer.viewBoxF()
        nat_w = vb.width() if vb.width() > 0 else 1.0
        nat_h = vb.height() if vb.height() > 0 else 1.0
        self._aspect = nat_w / nat_h

        # Wylicz rozmiar docelowy „boxu” przy zachowaniu proporcji
        size = self._compute_target_size(max_width, max_height)
        w, h = size.width(), size.height()  # <-- poprawka: pobieramy z QSize

        # Ustawienia rozmiaru widgetu (fixed => brak dalszego rozciągania przez layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(w, h)
        self.setMaximumSize(w, h)
        self.setFixedSize(w, h)

    def _compute_target_size(self, max_w: Optional[int], max_h: Optional[int]) -> QSize:
        if max_w and not max_h:
            tw = float(max_w)
            th = tw / self._aspect
        elif max_h and not max_w:
            th = float(max_h)
            tw = th * self._aspect
        elif max_w and max_h:
            box_aspect = float(max_w) / float(max_h)
            if self._aspect >= box_aspect:
                tw = float(max_w)
                th = tw / self._aspect
            else:
                th = float(max_h)
                tw = th * self._aspect
        else:
            tw = float(DEFAULT_MAX_LOGO_WIDTH or 160.0)
            th = tw / self._aspect
        return QSize(int(round(tw)), int(round(th)))

    def sizeHint(self) -> QSize:
        return self.maximumSize()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform,
            on=True
        )
        # Rysuj do pełnego prostokąta widgetu (proporcje zachowane przez fixed size)
        self._renderer.render(p, QRectF(0, 0, self.width(), self.height()))
        p.end()


class BrandingFooter(QWidget):
    """
    Stopka: logo SVG (wektorowe, proporcjonalne) + wyśrodkowany akapit tekstu + rząd hiperłączy.
    """

    def __init__(
        self,
        links: Optional[Iterable[Tuple[str, str]]] = None,
        logo_path: str = DEFAULT_LOGO_PATH,
        max_logo_width: Optional[int]  = DEFAULT_MAX_LOGO_WIDTH,
        max_logo_height: Optional[int] = DEFAULT_MAX_LOGO_HEIGHT,
        subtitle_text: Optional[str]   = DEFAULT_SUBTITLE_TEXT,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setObjectName("BrandingFooter")

        DEFAULT_LINKS = [
            ("Szkolenia OnGeo", "https://szkolenia.ongeo.pl/"),
			("Raporty o Terenie OnGeo", "https://ongeo.pl/"),
			("OnGeo Intelligence", "https://ongeo-intelligence.com/"),
        ]
        self._links: List[Tuple[str, str]] = list(links or DEFAULT_LINKS)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ───── LOGO (OSTRE, WEKTOROWE) ─────
        logo_wrap = QWidget(self)
        logo_lay = QHBoxLayout(logo_wrap)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo_lay.setSpacing(0)

        self.logo_widget = AspectRatioSvgWidget(
            svg_path=logo_path,
            max_width=max_logo_width,
            max_height=max_logo_height,
            parent=self
        )
        logo_lay.addStretch(1)
        logo_lay.addWidget(self.logo_widget, 0, Qt.AlignCenter)
        logo_lay.addStretch(1)
        root.addWidget(logo_wrap)

        # ───── PODPIS / AKAPIT POD LOGO ─────
        self.subtitle_label = QLabel(subtitle_text or "")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(0,0,0,0.65);
                font-size: 11px;
                padding: 2px 8px 0 8px;
            }
        """)
        root.addWidget(self.subtitle_label)

        # ───── LINKI ─────
        links_wrap = QWidget(self)
        links_lay = QHBoxLayout(links_wrap)
        links_lay.setContentsMargins(0, 0, 0, 0)
        links_lay.setSpacing(0)
        links_lay.addStretch(1)

        self._link_buttons: List[LinkButton] = []
        for title, url in self._links:
            btn = LinkButton(title, url, self)
            self._link_buttons.append(btn)
            links_lay.addWidget(btn, 0, Qt.AlignVCenter)
        links_lay.addStretch(1)
        root.addWidget(links_wrap)

        # ───── Stylizacja ─────
        self.setStyleSheet("""
            QWidget#BrandingFooter {
                border-top: 1px solid rgba(0,0,0,35);
                background: transparent;
            }
        """)

    # API do łatwego dodawania kolejnych linków
    def add_link(self, title: str, url: str):
        """Dodaje nowy hiperlink w stopce."""
        self._links.append((title, url))
        links_wrap = self.layout().itemAt(2).widget()  # 0: logo, 1: subtitle, 2: links
        links_lay: QHBoxLayout = links_wrap.layout()
        stretch_index = links_lay.count() - 1
        btn = LinkButton(title, url, self)
        self._link_buttons.append(btn)
        links_lay.insertWidget(stretch_index, btn, 0, Qt.AlignVCenter)
