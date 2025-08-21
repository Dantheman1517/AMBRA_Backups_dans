import pytest


avail_configs = ["a", "b"]
extra_configs = [1, 2]  # second dimension of configuration


@pytest.fixture(params=avail_configs, ids=lambda v: f"cfg-{v}")
def config(request):
    """Primary config values (string codes)."""
    return request.param


@pytest.fixture(params=extra_configs, ids=lambda v: f"extra-{v}")
def extra_config(request):
    """Secondary config values (numeric variants)."""
    return request.param


def test_delete_record(config, extra_config):
    pass


# def test_update_record_not_redcap_not_db(config, extra_config):
#     pass


# def test_update_record_not_redcap_in_db(config, extra_config):
#     pass


# def test_update_record_in_redcap_not_db(config, extra_config):
#     pass


# def test_update_record_in_redcap_in_db(config, extra_config):
#     pass



