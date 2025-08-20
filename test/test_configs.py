import pytest

# Example functions to test under each config

def func_a(cfg):
    return cfg["value"] * 2

def func_b(cfg):
    return cfg["value"] + 3

def func_c(cfg):
    return cfg["value"] - 1

def func_d(cfg):
    return cfg["value"] ** 2

def func_e(cfg):
    return cfg["value"]

@pytest.mark.parametrize("test_func", [func_a, func_b, func_c, func_d, func_e])
def test_functions(cfg, test_func):
    # Simple assertions to demonstrate pass/fail symbols
    result = test_func(cfg)
    assert result is not None
