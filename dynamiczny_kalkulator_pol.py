# -*- coding: utf-8 -*-
from typing import Optional, Dict, Tuple
import json
import os
from contextlib import contextmanager

from qgis.PyQt.QtWidgets import (
    QDockWidget, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QPushButton,
    QLabel, QLineEdit, QListWidget, QCheckBox, QMessageBox, QAction, QScrollArea,
    QListWidgetItem, QSizePolicy, QSpacerItem, QToolButton, QToolBar
)
from qgis.PyQt.QtCore import (
    Qt, QObject, QTimer, pyqtSlot, QSize,
    QCoreApplication, QTranslator, QSettings
)
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QFont, QColor

try:
    import sip
except Exception:
    sip = None

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsExpression, QgsExpressionContext,
    QgsExpressionContextUtils, QgsSettings, QgsFields,
    QgsApplication, QgsMessageLog, Qgis, QgsFeatureRequest, QgsField,
    QgsVectorDataProvider
)
from qgis.gui import QgsExpressionBuilderDialog

# ──────────────────────────────────────────────────────────────────────────────
# QRC RESOURCES – (paths :/plugins/…)
from . import resources_rc  # must be imported so :/ paths work

# ONGEO FOOTER (if you have plugin branding — keep this import)
try:
    from .qgis_branding.branding_footer import BrandingFooter
except Exception:
    BrandingFooter = None  # fallback when the module is missing

# ──────────────────────────────────────────────────────────────────────────────
# i18n (Qt) settings
PLUGIN_I18N_BASENAME = "dynamiczny_kalkulator_pol"  # file base for i18n/*.qm

# GUI names (source language: EN)
TOOLBAR_TITLE = "OnGeo Tools"
MENU_ROOT     = "OnGeo Tools"

# QSettings (internal keys - do not translate)
ORG = "DynamicznyKalkulatorPol"
KEY_LAST = "last_settings_json"

# ----------------- helpers -----------------
def _is_deleted(obj) -> bool:
    try:
        if obj is None:
            return True
        if sip is None:
            return False
        return sip.isdeleted(obj)
    except Exception:
        return True

def _log(msg: str):
    """Internal log helper (do not translate log prefix)."""
    try:
        QgsMessageLog.logMessage(f"DKP: {msg}", "Plugins", Qgis.Info)
    except Exception:
        pass

def _draw_text_icon(txt: str) -> QIcon:
    pm = QPixmap(24, 24); pm.fill(QColor(245,245,247))
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QColor(60,60,70)); p.setFont(QFont("Segoe UI", 10, QFont.Medium))
    p.drawText(pm.rect(), Qt.AlignCenter, txt); p.end()
    return QIcon(pm)

def _plugin_icon() -> QIcon:
    # Plugin icon from QRC (path prefix without _v1)
    forced = QIcon(":/plugins/Dynamiczny_kalkulator_pol/icon.svg")
    if not forced.isNull():
        return forced
    return _draw_text_icon("ε")

def _theme_icon_first(names) -> QIcon:
    for n in names:
        ico = QgsApplication.getThemeIcon(n)
        if not ico.isNull():
            return ico
    return QIcon()

def _get_or_create_toolbar(iface, title: str, object_name: str) -> QToolBar:
    """Find an existing toolbar with the given object name or create a new one.

    This allows multiple OnGeo plugins to share a single toolbar instead of creating duplicates.
    """
    mw = iface.mainWindow()
    for tb in mw.findChildren(QToolBar):
        if tb.objectName() == object_name:
            return tb

    tb = iface.addToolBar(title)
    tb.setObjectName(object_name)
    tb.setWindowTitle(title)
    tb.setToolTip(title)
    tb.setMovable(True)
    if tb.toggleViewAction():
        tb.toggleViewAction().setText(title)
    return tb

def _field_type_info(f: QgsField) -> Tuple[str, QIcon, str]:
    tn = (f.typeName() or "").lower()
    ico_text = _theme_icon_first(["mIconFieldText.svg"]) or _draw_text_icon("abc")
    ico_int  = _theme_icon_first(["mIconFieldInteger.svg"]) or _draw_text_icon("123")
    ico_real = _theme_icon_first([
        "mIconFieldDecimal.svg", "mIconFieldDouble.svg",
        "mIconFieldNumeric.svg", "mIconFieldFloat.svg", "mIconFieldNumber.svg"
    ]) or _draw_text_icon("1.23")
    ico_dt   = _theme_icon_first(["mIconFieldDateTime.svg"]) or _draw_text_icon("dt")
    ico_d    = _theme_icon_first(["mIconFieldDate.svg"]) or _draw_text_icon("date")
    ico_t    = _theme_icon_first(["mIconFieldTime.svg"]) or _draw_text_icon("time")
    ico_b    = _theme_icon_first(["mIconFieldBoolean.svg"]) or _draw_text_icon("bool")

    # NOTE: these labels are currently not shown directly in the UI, but we keep them in EN.
    if "char" in tn or "text" in tn or "string" in tn:  return ("abc", ico_text, "Text")
    if "int" in tn:                                     return ("123", ico_int, "Integer")
    if any(x in tn for x in ["real","double","float","numeric","decimal"]):
                                                        return ("1.23", ico_real, "Real")
    if "datetime" in tn or ("date" in tn and "time" in tn):
                                                        return ("dt",  ico_dt,  "DateTime")
    if "date" in tn:                                    return ("date",ico_d,   "Date")
    if "time" in tn:                                    return ("time",ico_t,   "Time")
    if "bool" in tn or "bit" in tn:                     return ("bool",ico_b,   "Boolean")
    try:
        if f.isNumeric():                               return ("1.23", ico_real, "Numeric")
    except Exception:
        pass
    return ("?", _draw_text_icon("?"), f.typeName() or "Unknown")

def _coerce_to_field_type(val, qgs_field: QgsField):
    """Gently cast the expression result to the field data type."""
    try:
        tname = (qgs_field.typeName() or "").lower()
        if qgs_field.isNumeric():
            if "int" in tname:
                if val in ("", None): return None
                return int(float(val))
            else:
                if val in ("", None): return None
                return float(val)
        if "bool" in tname:
            if isinstance(val, str):
                return val.strip().lower() in ("1","true","t","yes","y")
            return bool(val)
        if val is None:
            return None
        return str(val) if not isinstance(val, (str, bytes)) else val
    except Exception:
        return val

@contextmanager
def block_layer_signals(layer: QgsVectorLayer):
    """Context manager: safely blocks layer signals during modifications."""
    eb = layer.editBuffer()
    try:
        if eb: eb.blockSignals(True)
        layer.blockSignals(True)
        yield
    finally:
        if eb: eb.blockSignals(False)
        layer.blockSignals(False)

# --------------- Plugin main ---------------
class FieldCalcDockPlugin(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        # Keep translator alive (Qt translator must be stored to avoid GC)
        self.translator: Optional[QTranslator] = None
        self._install_translator()

        self.dock: Optional[FieldCalcDock] = None
        self.toolbar_action: Optional[QAction] = None
        self.toolbar = None
        self._project = QgsProject.instance()
        self._connected = False
        self._lt_name_conn_root = None
        self._lt_name_conn_slot = None

    # ---------- i18n loader ----------
    def _install_translator(self):
        """Load and install the .qm translation matching current QGIS UI locale."""
        try:
            locale_full = QSettings().value('locale/userLocale', 'en')
            locale = str(locale_full)[0:2] if locale_full else "en"
        except Exception:
            locale = "en"

        locale_path = os.path.join(
            os.path.dirname(__file__),
            'i18n',
            f'{PLUGIN_I18N_BASENAME}_{locale}.qm'
        )

        if os.path.exists(locale_path):
            tr = QTranslator()
            if tr.load(locale_path):
                QCoreApplication.installTranslator(tr)
                self.translator = tr
                _log(f"Loaded translation: {locale_path}")
            else:
                _log(f"Failed to load translation file: {locale_path}")
        else:
            # No translation file for this locale -> fall back to source strings (EN)
            self.translator = None

    def initGui(self):
        # "OnGeo Tools" toolbar – shared with other OnGeo plugins
        self.toolbar = _get_or_create_toolbar(self.iface, self.tr(TOOLBAR_TITLE), "NarzędziaOnGeoToolbar")

        # Plugin action
        self.toolbar_action = QAction(
            QIcon(":/plugins/Dynamiczny_kalkulator_pol/icon.svg"),
            self.tr("Dynamic Field Calculator"),
            self.iface.mainWindow()
        )
        self.toolbar_action.setObjectName("dynamiczny_kalkulator_pol_action")
        self.toolbar_action.setCheckable(True)
        self.toolbar_action.toggled.connect(self._on_action_toggled)

        self.toolbar.addAction(self.toolbar_action)
        self.iface.addPluginToMenu(self.tr(MENU_ROOT), self.toolbar_action)

        self._connect_project_signals()

        if self.toolbar_action.icon().isNull():
            self.toolbar_action.setIcon(_plugin_icon())

    def unload(self):
        try:
            if self._lt_name_conn_root and self._lt_name_conn_slot:
                self._lt_name_conn_root.nameChanged.disconnect(self._lt_name_conn_slot)
        except Exception:
            pass
        self._lt_name_conn_root = None
        self._lt_name_conn_slot = None

        if self.dock:
            try: self.dock.visibilityChanged.disconnect(self._sync_action_with_dock)
            except Exception: pass
            try: self.dock.destroyed.disconnect(self._on_dock_destroyed)
            except Exception: pass

        if self.toolbar_action:
            try:
                if self.toolbar:
                    self.toolbar.removeAction(self.toolbar_action)

                # Remove from the translated menu root (current locale)
                self.iface.removePluginMenu(self.tr(MENU_ROOT), self.toolbar_action)

                # Backward-compat cleanup: remove possible old PL menu root
                try:
                    self.iface.removePluginMenu("Narzędzia OnGeo", self.toolbar_action)
                except Exception:
                    pass
                try:
                    self.iface.removePluginMenu("Dynamiczny Kalkulator Pól", self.toolbar_action)
                except Exception:
                    pass
            except Exception:
                pass

        self.toolbar = None
        self._disconnect_project_signals()

    def _connect_project_signals(self):
        if self._connected:
            return
        p = self._project
        p.layersAdded.connect(self._on_layers_changed)
        p.layerWasAdded.connect(self._on_layers_changed)
        p.layersRemoved.connect(self._on_layers_changed)
        p.cleared.connect(self._on_layers_changed)
        self._connected = True

    def _disconnect_project_signals(self):
        if not self._connected:
            return
        p = self._project
        for sig in (p.layersAdded, p.layerWasAdded, p.layersRemoved, p.cleared):
            try:
                sig.disconnect(self._on_layers_changed)
            except Exception:
                pass
        self._connected = False

    def _on_layers_changed(self, *_a, **_k):
        if self.dock and not _is_deleted(self.dock):
            QTimer.singleShot(0, self.dock.refresh_layers)

    def _on_action_toggled(self, checked: bool):
        if self.dock is None:
            self.dock = FieldCalcDock(self.iface)
            self.dock.refresh_layers()
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.visibilityChanged.connect(self._sync_action_with_dock)
            self.dock.destroyed.connect(self._on_dock_destroyed)
            root = QgsProject.instance().layerTreeRoot()
            root.nameChanged.connect(self.dock.refresh_layers, Qt.QueuedConnection)
            self._lt_name_conn_root = root
            self._lt_name_conn_slot = self.dock.refresh_layers
        self.dock.setVisible(bool(checked))
        if self.toolbar_action and self.toolbar_action.icon().isNull():
            self.toolbar_action.setIcon(_plugin_icon())

    def _sync_action_with_dock(self, visible: bool):
        # Prevents a toggled→visible→toggled cascade when docks are rearranged
        if self.toolbar_action:
            self.toolbar_action.blockSignals(True)
            try:
                self.toolbar_action.setChecked(bool(visible))
            finally:
                self.toolbar_action.blockSignals(False)

    def _on_dock_destroyed(self, *_args):
        try:
            if getattr(self, "_lt_name_conn_root", None) and getattr(self, "_lt_name_conn_slot", None):
                self._lt_name_conn_root.nameChanged.disconnect(self._lt_name_conn_slot)
        except Exception:
            pass
        self._lt_name_conn_root = None
        self._lt_name_conn_slot = None
        self.dock = None
        if self.toolbar_action:
            self.toolbar_action.setChecked(False)

# --------------- Dock / UI -----------------
class FieldCalcDock(QDockWidget):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        self.setWindowTitle(self.tr("Dynamic Field Calculator"))
        self.setObjectName("DynamicFieldCalculatorDock")

        # ► Allow ALL dock widget areas (top/bottom/left/right)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        # Good dock properties (movable, floatable, closable)
        self.setFeatures(
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )

        self._settings = QgsSettings(ORG)

        # Reaction to dock location change (stabilization for top/bottom)
        self.dockLocationChanged.connect(self._on_dock_location_changed)

        # Main dock widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        # Outer vertical layout: [functional area] above [footer]
        outer_vbox = QVBoxLayout(self.main_widget)
        outer_vbox.setContentsMargins(0, 0, 0, 0)
        outer_vbox.setSpacing(0)

        # FUNCTIONAL AREA
        self.main_area = QWidget(self.main_widget)
        outer_vbox.addWidget(self.main_area, 1)
        self.main_layout = QHBoxLayout(self.main_area)

        # LEFT COLUMN
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(6)

        self.layer_combo = QComboBox()
        self.left_layout.addWidget(QLabel(self.tr("Choose layer:")))
        self.left_layout.addWidget(self.layer_combo)
        self.layer_combo.currentIndexChanged.connect(self.load_fields)

        self.field_list = QListWidget()
        self.field_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.left_layout.addWidget(QLabel(self.tr("Select attributes to update:")))
        self.left_layout.addWidget(self.field_list, 1)

        self.only_selected = QCheckBox(self.tr("Selected features only"))
        self.left_layout.addWidget(self.only_selected)

        btn_row = QHBoxLayout()
        self.add_field_button = QPushButton(self.tr("Add selected fields to edit list"))
        self.reset_button = QPushButton(self.tr("Clear panel"))
        btn_row.addWidget(self.add_field_button)
        btn_row.addWidget(self.reset_button)
        self.left_layout.addLayout(btn_row)

        self.hint = QLabel(
            self.tr(
                "Update multiple attributes in one panel.<br>"
                "Enter expressions using QGIS expression syntax.<br>"
                "You can also click the calculator icon to open the Expression Builder.<br>"
                "<b>NOTE:</b> When updating large datasets, wait until the operation finishes."
            )
        )
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(
            "QLabel{background:#f5f5f7;border:1px solid #d6d6dc;"
            "border-radius:6px;padding:6px;color:#333;}"
        )
        self.left_layout.addWidget(self.hint)

        # RIGHT COLUMN
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(6)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.expr_container = QWidget()
        self.expression_layout = QVBoxLayout(self.expr_container)
        self.expression_layout.setContentsMargins(6, 6, 6, 6)
        self.expression_layout.setSpacing(6)  # fixed spacing

        # Fixed spacer at the bottom: keeps rows from "floating" when resizing the dock
        self._expr_bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.expression_layout.addItem(self._expr_bottom_spacer)

        self.scroll.setWidget(self.expr_container)
        self.right_layout.addWidget(self.scroll, 1)

        actions_column = QVBoxLayout()
        self.apply_button = QPushButton(self.tr("Apply (no commit)"))
        self.commit_button = QPushButton(self.tr("Commit changes to layer"))
        self.rollback_button = QPushButton(self.tr("Discard changes"))
        self.save_last_button = QPushButton(self.tr("Save field configuration"))
        self.load_last_button = QPushButton(self.tr("Load saved configuration"))
        for b in [self.apply_button, self.commit_button, self.rollback_button,
                  self.save_last_button, self.load_last_button]:
            actions_column.addWidget(b)
        self.right_layout.addLayout(actions_column)

        # MERGE COLUMNS
        self.main_layout.addWidget(self.left_panel, 0)
        self.main_layout.addWidget(self.right_panel, 1)

        # ONGEO FOOTER (if the import is available)
        if BrandingFooter is not None:
            self.footer = BrandingFooter()
            fwrap = QWidget(self.main_widget)
            fw_lay = QVBoxLayout(fwrap)
            fw_lay.setContentsMargins(6, 6, 6, 6)
            fw_lay.setSpacing(0)
            fw_lay.addWidget(self.footer)
            outer_vbox.addWidget(fwrap, 0, Qt.AlignBottom)

        # DATA MODELS
        self.expression_inputs: Dict[str, QLineEdit] = {}
        self.expression_rows: Dict[str, QWidget] = {}

        # SIGNALS
        self.add_field_button.clicked.connect(self.prepare_expression_inputs)
        self.reset_button.clicked.connect(self.reset_ui)
        self.apply_button.clicked.connect(self.apply_changes)
        self.commit_button.clicked.connect(self.commit_changes)
        self.rollback_button.clicked.connect(self.rollback_changes)
        self.save_last_button.clicked.connect(self.save_last_settings)
        self.load_last_button.clicked.connect(self.load_last_settings)

        self.refresh_layers()

    def _on_dock_location_changed(self, area: Qt.DockWidgetArea):
        """
        Size stabilization when docked at the top/bottom areas.
        It does not limit functionality, but prevents extreme relayouts.
        """
        # size policy: flexible width, preferred height
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
            # reasonable minimum height in horizontal orientation
            self.setMinimumHeight(220)
        else:
            # on the sides: no hard minimum height
            self.setMinimumHeight(0)

    # ---------- Icon for expression builder ----------
    def _expression_button_icon(self) -> QIcon:
        """Returns an icon for the expression builder button – forced SVG from QRC."""
        res = QIcon(":/plugins/Dynamiczny_kalkulator_pol/calc_button.svg")
        if not res.isNull():
            return res
        theme = _theme_icon_first(["mIconExpression.svg", "mIconExpressionFunction.svg"])
        if not theme.isNull():
            return theme
        return _draw_text_icon("fx")

    # ---------- Layers / Fields ----------
    @pyqtSlot()
    def refresh_layers(self):
        if _is_deleted(self) or self.widget() is None:
            return
        current = self.current_layer()
        current_id = current.id() if current else None

        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer.id())
        self.layer_combo.blockSignals(False)

        if current_id:
            idx = self.layer_combo.findData(current_id)
            if idx >= 0:
                self.layer_combo.setCurrentIndex(idx)
        elif self.layer_combo.count() > 0:
            self.layer_combo.setCurrentIndex(0)

        self.load_fields()

    def current_layer(self) -> Optional[QgsVectorLayer]:
        try:
            layer_id = self.layer_combo.currentData()
            if not layer_id:
                return None
            layer = QgsProject.instance().mapLayer(layer_id)
            if isinstance(layer, QgsVectorLayer):
                return layer
        except Exception:
            pass
        return None

    def load_fields(self):
        """Load the list of editable fields of the current layer."""
        self.field_list.clear()
        layer = self.current_layer()
        if not layer:
            return

        fields = layer.fields()
        for f in fields:
            idx = fields.indexFromName(f.name())
            if idx < 0:
                continue
            if fields.fieldOrigin(idx) == QgsFields.OriginExpression:
                continue
            try:
                if f.isReadOnly():
                    continue
            except Exception:
                pass
            badge, icon, _pretty = _field_type_info(f)
            item = QListWidgetItem(icon, f.name())
            item.setData(Qt.UserRole, (f.name(), badge, _pretty))
            self.field_list.addItem(item)

    # ---------- Creation of editing rows ----------
    def add_expression_input(self, field_name: str):
        """Create an editing row for the given field."""
        if field_name in self.expression_inputs:
            return

        layer = self.current_layer()
        fields = layer.fields() if layer else None
        f = fields.field(field_name) if (fields and fields.indexOf(field_name) != -1) else None
        if f is None:
            badge = "?"
        else:
            badge, _, _ = _field_type_info(f)

        row = QWidget()
        # The row does not grow in height – fixed spacing between rows
        row.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        label = QLabel(f"<b>{field_name}</b> <span style='color:#666;'>[{badge}]</span>")
        label.setTextFormat(Qt.RichText)

        edit = QLineEdit()

        # ► QToolButton with forced icon (SVG) – expression builder
        browse_btn = QToolButton()
        browse_btn.setToolTip(self.tr("Expression Builder"))
        browse_btn.setIcon(self._expression_button_icon())
        # Icon and button size adjusted to the line edit
        h = max(24, edit.sizeHint().height())
        browse_btn.setIconSize(QSize(h - 8, h - 8))
        browse_btn.setFixedSize(QSize(h, h))
        # Subtle frame similar to the previous one
        browse_btn.setStyleSheet(
            "QToolButton{border:1px solid #c9c9cf;border-radius:4px;background:#ffffff;}"
            "QToolButton:hover{background:#f3f6ff;}"
            "QToolButton:pressed{background:#e8eefc;}"
        )

        remove_btn = QPushButton(self.tr("Remove"))
        remove_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        remove_btn.setFixedHeight(h)

        browse_btn.clicked.connect(lambda _, e=edit: self.open_expression_builder(e))
        remove_btn.clicked.connect(lambda _, fname=field_name: self.remove_expression_input(fname))

        lay.addWidget(label)
        lay.addWidget(edit, 1)
        lay.addWidget(browse_btn, 0)
        lay.addWidget(remove_btn, 0)

        # Insert before the bottom spacer so the spacer is always the last item
        idx_sp = self.expression_layout.indexOf(self._expr_bottom_spacer)
        if idx_sp < 0:
            # Safety: add the spacer again if it was removed
            self._expr_bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.expression_layout.addItem(self._expr_bottom_spacer)
            idx_sp = self.expression_layout.indexOf(self._expr_bottom_spacer)
        self.expression_layout.insertWidget(idx_sp, row)

        self.expression_inputs[field_name] = edit
        self.expression_rows[field_name] = row

    def prepare_expression_inputs(self):
        """Add rows for currently selected items in the field list."""
        for i in range(self.field_list.count()):
            item = self.field_list.item(i)
            if not item.isSelected():
                continue
            field_name = item.data(Qt.UserRole)[0] if item.data(Qt.UserRole) else item.text()
            self.add_expression_input(field_name)

    def remove_expression_input(self, field_name: str):
        w = self.expression_rows.pop(field_name, None)
        if w:
            w.setParent(None)
            w.deleteLater()
            self.expression_inputs.pop(field_name, None)

    def open_expression_builder(self, target_line_edit: QLineEdit):
        layer = self.current_layer()
        if not layer:
            QMessageBox.information(self, self.tr("No layer"), self.tr("Choose a layer first."))
            return
        dlg = QgsExpressionBuilderDialog(layer, target_line_edit.text(), self)
        if dlg.exec_():
            target_line_edit.setText(dlg.expressionText())

    # ---------- Operations ----------
    def apply_changes(self):
        layer = self.current_layer()
        if not layer:
            QMessageBox.warning(self, self.tr("No layer"), self.tr("Choose a vector layer."))
            return
        if not self.expression_inputs:
            QMessageBox.information(self, self.tr("No fields"), self.tr("Add at least one field to edit."))
            return

        # Provider capabilities
        caps = layer.dataProvider().capabilities()
        if not (caps & QgsVectorDataProvider.ChangeAttributeValues):
            QMessageBox.warning(self, self.tr("No permissions"), self.tr("This layer does not support attribute editing."))
            return

        if not layer.isEditable():
            if not layer.startEditing():
                QMessageBox.critical(self, self.tr("Error"), self.tr("Cannot start editing this layer."))
                return

        only_selected = self.only_selected.isChecked()

        # Prepare and validate expressions + dependency analysis
        expressions: Dict[str, QgsExpression] = {}
        field_index: Dict[str, int] = {}
        needed_attrs = set()
        needs_geom = False

        ctx = QgsExpressionContext()
        ctx.appendScope(QgsExpressionContextUtils.globalScope())
        ctx.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        ctx.appendScope(QgsExpressionContextUtils.layerScope(layer))

        for field, w in self.expression_inputs.items():
            text = (w.text() or "").strip()
            if not text:
                continue
            exp = QgsExpression(text)
            if exp.hasParserError():
                QMessageBox.critical(
                    self,
                    self.tr("Expression error"),
                    self.tr("[{field}] {err}").format(field=field, err=exp.parserErrorString())
                )
                return
            # Prepare + analyze dependencies
            exp.prepare(ctx)
            for c in exp.referencedColumns():
                needed_attrs.add(c)
            needs_geom = needs_geom or exp.needsGeometry()

            expressions[field] = exp
            field_index[field] = layer.fields().indexFromName(field)

        if not expressions:
            QMessageBox.information(self, self.tr("No expressions"), self.tr("Fill in expressions for the selected fields."))
            return

        # Build feature request: only necessary data
        req = QgsFeatureRequest()
        if only_selected:
            fids = list(layer.selectedFeatureIds())
            if fids:
                req.setFilterFids(fids)
            else:
                QMessageBox.information(self, self.tr("No selection"), self.tr("No features are selected."))
                return

        if not needs_geom:
            req.setFlags(QgsFeatureRequest.NoGeometry)

        if needed_attrs:
            idxs = [layer.fields().indexFromName(n) for n in needed_attrs if layer.fields().indexFromName(n) != -1]
            req.setSubsetOfAttributes(idxs)
        else:
            # No columns needed — empty list speeds up the provider
            req.setSubsetOfAttributes([])

        total_changes = 0
        processed = 0

        try:
            with block_layer_signals(layer):
                # Visible in undo stack -> translate
                layer.beginEditCommand(self.tr("DKP: apply expressions (preview)"))

                for ftr in layer.getFeatures(req):
                    ctx.setFeature(ftr)
                    for field_name, exp in expressions.items():
                        idx = field_index.get(field_name, -1)
                        if idx < 0:
                            continue
                        val = exp.evaluate(ctx)
                        if exp.hasEvalError():
                            raise RuntimeError(f"[{field_name}] {exp.evalErrorString()}")

                        # Match the result type to the field type
                        try:
                            val = _coerce_to_field_type(val, layer.fields()[idx])
                        except Exception:
                            pass

                        ok = layer.changeAttributeValue(ftr.id(), idx, val)
                        if not ok:
                            raise RuntimeError(
                                self.tr("Failed to change {field} for feature FID={fid}").format(
                                    field=field_name, fid=ftr.id()
                                )
                            )
                        total_changes += 1

                    processed += 1
                    if processed % 500 == 0:
                        QgsApplication.processEvents()

                layer.endEditCommand()

        except Exception as e:
            try:
                layer.destroyEditCommand()
            except Exception:
                pass
            QMessageBox.critical(self, self.tr("Error"), self.tr("Operation aborted: {err}").format(err=e))
            return

        layer.triggerRepaint()
        QMessageBox.information(
            self,
            self.tr("Done"),
            self.tr(
                "Expressions applied to the selected attributes.\n"
                "Number of changed values: {n}\n"
                "Remember to commit the changes."
            ).format(n=total_changes)
        )

    def commit_changes(self):
        layer = self.current_layer()
        if layer and layer.isEditable():
            if layer.commitChanges():
                QMessageBox.information(self, self.tr("Committed"), self.tr("Changes committed to the layer (editing stopped)."))
            else:
                errs = layer.commitErrors() or []
                layer.rollBack()
                msg = self.tr("Commit failed.")
                if errs:
                    msg += self.tr("\n\nDetails:\n- ") + "\n- ".join(errs)
                QMessageBox.critical(self, self.tr("Error"), msg)

    def rollback_changes(self):
        layer = self.current_layer()
        if layer and layer.isEditable():
            layer.rollBack()
            QMessageBox.information(self, self.tr("Discarded"), self.tr("Uncommitted changes were discarded (editing stopped)."))

    # ---------- Save / Load ----------
    def save_last_settings(self):
        layer = self.current_layer()
        data = {
            "layer_name": layer.name() if layer else "",
            "only_selected": self.only_selected.isChecked(),
            "expressions": {f: w.text() for f, w in self.expression_inputs.items()},
        }
        self._settings.setValue(KEY_LAST, json.dumps(data))
        QMessageBox.information(self, self.tr("Saved"), self.tr("Current settings were saved as the last configuration."))

    def load_last_settings(self):
        raw = self._settings.value(KEY_LAST, "")
        if not raw:
            QMessageBox.information(self, self.tr("No data"), self.tr("No saved settings found yet."))
            return
        try:
            data = json.loads(raw)
        except Exception:
            QMessageBox.warning(self, self.tr("Data error"), self.tr("Cannot read the saved settings."))
            return

        self.reset_ui()

        target = data.get("layer_name", "")
        if target:
            for i in range(self.layer_combo.count()):
                if self.layer_combo.itemText(i) == target:
                    self.layer_combo.setCurrentIndex(i)
                    break

        self.only_selected.setChecked(bool(data.get("only_selected", False)))
        exprs = data.get("expressions", {}) or {}

        for field_name in exprs.keys():
            self.add_expression_input(field_name)

        for f, t in exprs.items():
            if f in self.expression_inputs:
                self.expression_inputs[f].setText(t)

    def reset_ui(self):
        for w in list(self.expression_rows.values()):
            w.setParent(None)
            w.deleteLater()
        self.expression_rows.clear()
        self.expression_inputs.clear()

        # Restore the bottom spacer (in case it was removed)
        while True:
            idx = self.expression_layout.indexOf(self._expr_bottom_spacer)
            if idx == -1:
                break
            item = self.expression_layout.takeAt(idx)
            del item
        self._expr_bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.expression_layout.addItem(self._expr_bottom_spacer)

        self.field_list.clearSelection()
        self.load_fields()
