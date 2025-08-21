
import pytest


instrument_name = 'test_form'
avail_instances = [None, 1, 2]
avail_actions = ['Create', 'Update', 'Delete']
avail_fields = [
    [{'redcap_variable' : 'pytest_text', 'value' : 'This is a test text input', 'field_type' : 'text'}],
    [{'redcap_variable' : 'pytest_radio', 'value' : '2', 'field_type' : 'radio'}],
    [{'redcap_variable' : 'pytest_file_upload', 'value' : '1234567', 'field_type' : 'file'}]
]
avail_verified = [0, 1]

avail_long_status = [True, False]
avail_arm_num = [1, 2]
avail_num_of_arms = [1, 2]
avail_arm_names = ['Arm 1_test', 'Arm 2_test']
avail_num_of_events = [1, 2]
avail_events = [
    {'label' : 'Event 1', 'redcap_event_name' : 'event_1_arm_1'}, 
    {'label' : 'Event 2', 'redcap_event_name' : 'event_2_arm_1'}
]


log_info = {
    'patient_name' : '9999',
    'instrument_name' : instrument_name,
    'instance' : avail_instances[1],
    'action' : avail_actions[0],
    'fields': avail_fields[0],
    'verified' : avail_verified[0]
}

proj_config = {
    'is_longitudinal' : avail_long_status[1], 
    'num_of_arms' : avail_num_of_arms[1], 
    'arm_num' : avail_arm_num[0], 
    'arm_name' : avail_arm_names[1], 
    'num_of_events' : avail_num_of_events[0], 
    'event' : avail_events[0]
}


@pytest.fixture(params=log_configs, ids=lambda v: f"cfg-{v}")
def config(request):
    """Primary config values (string codes)."""
    return request.param


@pytest.fixture(params=project_configs, ids=lambda v: f"extra-{v}")
def project_config(request):
    """Secondary config values (numeric variants)."""
    return request.param



def test_delete_record(config, project_config):


    


    pass


# def test_update_record_not_redcap_not_db(config, project_config):
#     pass


# def test_update_record_not_redcap_in_db(config, project_config):
#     pass


# def test_update_record_in_redcap_not_db(config, project_config):
#     pass


# def test_update_record_in_redcap_in_db(config, project_config):
#     pass