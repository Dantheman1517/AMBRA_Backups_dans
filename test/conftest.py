import re
import pytest

# ---------------------------------------------------------------------------
# Configuration objects you want to iterate over
CONFIGS = [
    {"name": "config1", "value": 1},
    {"name": "config2", "value": 2},
]


@pytest.fixture(params=CONFIGS, ids=lambda c: c["name"])  # id becomes part inside []
def cfg(request):
    return request.param


_GROUPING_STATE = {"current": None, "terminal": None}
_GROUPING_RESULTS = {}


def pytest_configure(config):  # Called once – grab terminal reporter safely
    _GROUPING_STATE["terminal"] = config.pluginmanager.get_plugin("terminalreporter")


def _extract_config_id(nodeid: str) -> str:
    m = re.search(r"\[(.+)\]$", nodeid)
    if not m:
        return ""
    param_id = m.group(1)
    # tokens separated by '-' (pytest combines parametrizations in order applied)
    for token in param_id.split('-'):
        if token.startswith('config'):
            return token
    return ""


def pytest_collection_modifyitems(session, config, items):
    # Reorder so all tests for config1 appear before config2, etc.
    items.sort(key=lambda i: (_extract_config_id(i.nodeid), i.nodeid))
    # Initialize result store in declared order
    for c in CONFIGS:
        _GROUPING_RESULTS.setdefault(c["name"], [])


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    config_id = _extract_config_id(report.nodeid)
    if not config_id:
        return
    symbol = "." if report.passed else ("F" if report.failed else ("S" if report.skipped else "?"))
    _GROUPING_RESULTS.setdefault(config_id, []).append(symbol)


def pytest_report_teststatus(report, config):
    # Suppress real-time progress symbols; still keep outcome classification
    if report.when == "call":
        return report.outcome, "", report.outcome.upper()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    # Print desired grouped output at end
    terminalreporter.write_line("")
    for c in CONFIGS:
        cid = c["name"]
        symbols = _GROUPING_RESULTS.get(cid, [])
        if not symbols:
            continue
        terminalreporter.write_line(f"{cid}:")
        terminalreporter.write_line(" ".join(symbols))
    terminalreporter.write_line("")
