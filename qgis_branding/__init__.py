# qgis_branding/__init__.py
# Purpose: register Qt resources (QRC) on import.
try:
    from . import branding_rc  # noqa: F401
    QRC_REGISTERED = True
except Exception:
    QRC_REGISTERED = False
