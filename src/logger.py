"""Append-mode CSV logger for ATMOS calculations."""
import datetime
import logging
import pathlib

from config import APP_CONFIG

_LOG_PATH = pathlib.Path(APP_CONFIG["log_file"])

_logger = logging.getLogger("atmos")
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    _handler = logging.FileHandler(_LOG_PATH, mode="a")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    # Write CSV header only when creating a new / empty file
    is_new = (not _LOG_PATH.exists()) or (_LOG_PATH.stat().st_size == 0)
    if is_new:
        _logger.info("timestamp,alt_ft,Mach,KTAS,KEAS,KCAS,q_psf")


def log_speed_result(alt_ft, result):
    """Log a speed conversion result (dict with Mach/ktas/keas/kcas/q_c keys)."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _logger.info(
        f"{ts},{alt_ft:.1f},{result['Mach']:.4f},"
        f"{result['ktas']:.1f},{result['keas']:.1f},{result['kcas']:.1f},{result['q_c']:.3f}"
    )


def log_atmos_result(result):
    """Log an atmospheric properties result (dict with h_press_ft/p_static_psf keys)."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _logger.info(
        f"{ts},{result['h_press_ft']:.1f},,,,,"
        f"{result['p_static_psf']:.3f}"
    )
