"""Regression tests for the computation engine and the pyplot-free chart path."""
import io
import threading

import pytest
from matplotlib.figure import Figure

import atmos
from atmos import plot_speed_alt

NELSON = atmos.list_models()["standard_atmos.csv"]
USSA76 = atmos.list_models()["standard_atmos_1976.csv"]


def test_shipped_files_listed():
    assert set(atmos.list_models()) == {"standard_atmos.csv", "standard_atmos_1976.csv"}
    assert "speed_envelope_example.json" in atmos.list_envelopes()


def test_mach_alt_known_point():
    # Values recorded from ATMOS 1.0.0 (Nelson model) before the packaging change.
    with atmos.use_model(NELSON):
        speeds = atmos.mach_alt(0.84, 35000)
    assert speeds["ktas"] == pytest.approx(484.2413, abs=1e-3)
    assert speeds["keas"] == pytest.approx(269.8749, abs=1e-3)
    assert speeds["kcas"] == pytest.approx(287.4799, abs=1e-3)
    assert speeds["q_c"] == pytest.approx(293.2635, abs=1e-3)


def test_cas_alt_supersonic_known_point():
    with atmos.use_model(NELSON):
        speeds = atmos.cas_alt(700, 10000)
    assert speeds["Mach"] == pytest.approx(1.229688, abs=1e-5)
    assert speeds["ktas"] == pytest.approx(784.8356, abs=1e-3)


def test_atmos_prop_pres_known_point():
    with atmos.use_model(NELSON):
        props = atmos.get_atmos_prop_pres(499.34)
    assert props["h_press_ft"] == pytest.approx(34941.0)
    assert props["temp_degR"] == pytest.approx(394.064)


def test_out_of_range_raises():
    with atmos.use_model(NELSON):
        with pytest.raises(atmos.AtmosRangeError):
            atmos.get_atmos_prop_alt(10_000_000)


def test_use_model_restores_previous():
    atmos.set_atmos_model(NELSON)
    with atmos.use_model(USSA76):
        ktas_76 = atmos.mach_alt(0.84, 35000)["ktas"]
    assert ktas_76 == pytest.approx(484.3135, abs=1e-3)
    assert atmos.mach_alt(0.84, 35000)["ktas"] == pytest.approx(484.2413, abs=1e-3)


def test_model_choice_is_per_thread():
    results = {}
    barrier = threading.Barrier(2)

    def run(name, path):
        with atmos.use_model(path):
            barrier.wait()  # both threads have set their model before either computes
            results[name] = atmos.mach_alt(0.84, 35000)["ktas"]

    threads = [threading.Thread(target=run, args=a) for a in (("nelson", NELSON), ("ussa76", USSA76))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["nelson"] == pytest.approx(484.2413, abs=1e-3)
    assert results["ussa76"] == pytest.approx(484.3135, abs=1e-3)


@pytest.mark.parametrize("x_type", ["ktas", "kcas", "keas"])
def test_draw_speed_alt_on_bare_figure(x_type):
    fig = Figure(figsize=plot_speed_alt.FIGSIZE_IN)
    with atmos.use_model(NELSON):
        plot_speed_alt.draw_speed_alt(fig, x_type, atmos.list_envelopes()["speed_envelope_example.json"])
    buf = io.StringIO()
    fig.savefig(buf, format="svg")
    assert buf.getvalue().lstrip().startswith("<?xml")
