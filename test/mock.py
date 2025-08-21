"""

Class for creating mock records and logs for testing purposes in a REDCap project.
Creates mock based on record and project configurations
"""

from datetime import datetime
import pandas as pd


################################################################################
class Mock():
    # --------------------------------------------------------------------------
    def __init__(self, project, log_info, proj_config):
        self.project = project
        self.log_info = log_info
        self.proj_config = proj_config
        self.check_info_configs()
        self.expose_vars()

        self.mock_log = self.create_mock_log()
        self.mock_record = self.create_mock_record()
        self.mock_db = self.make_db_format_record()

    # --------------------------------------------------------------------------
    def check_info_configs(self):
        """
        TODO:
        - check that unqiue event name and label work for the expected project
        """

        standard_info = set(['patient_name', 'instance', 'instrument_name', 'action', 'fields', 'verified'])
        standard_info_configs = set(['is_longitudinal', 'num_of_arms', 'arm_num', 'arm_name', 'event', 'num_of_events'])
        
        info_missing = set(standard_info) - set(self.log_info.keys())
        if info_missing:
            raise ValueError(f"Missing following record info: {info_missing}")
        configs_missing = set(standard_info_configs) - set(self.proj_config.keys())
        if configs_missing:
            raise ValueError(f"Missing following mock configs: {configs_missing}")
        
    # --------------------------------------------------------------------------
    def expose_vars(self):

        self.patient_name = self.log_info['patient_name']
        self.instrument_name = self.log_info['instrument_name']
        self.fields = self.log_info['fields']
        self.num_fields = len(self.fields)
        self.instance = self.log_info['instance']
        self.verified = self.log_info['verified']
        self.action = self.log_info['action'].capitalize()
        if self.action not in ["Create", "Update", "Delete"]:
            raise ValueError("Action must be one of 'Create', 'Update', or 'Delete'")
        self.deleted = 1 if self.action == 'Delete' else 0

        self.num_of_arms = self.proj_config["num_of_arms"]
        self.arm_num = self.proj_config["arm_num"]
        self.arm_name = self.proj_config["arm_name"]
        self.event_label = self.proj_config["event"]['label']
        self.redcap_event_name = self.proj_config["event"]['redcap_event_name']
        self.num_of_events = self.proj_config["num_of_events"]

    # --------------------------------------------------------------------------
    def create_mock_log(self):
        """        
        TODO:
        - add ability to use verified and deleted fields
        """

        mock_log = {
            "timestamp": datetime.now(),
            "username": "test_user",
            "record": self.patient_name,
        }

        if "is_longitudinal" in self.proj_config:        

            if self.num_of_arms == 1:
            
                if self.num_of_events == 1:
                    # api does not specify arm or event when only 1 for each
                    mock_log['action'] = f'{self.action} record {self.patient_name}'

                elif self.num_of_events > 1:
                    if self.action == 'Create' or self.action == 'Update':
                        # needs to specify the event name if multiple events
                        mock_log['action'] = f'{self.action} record {self.patient_name} ({self.event_label})'
                    elif self.action == 'Delete':            
                        # deleting one record deletes all events
                        mock_log['action'] = f'{self.action} record {self.patient_name}'

            elif self.num_of_arms > 1:

                if self.action == 'Create' or self.action == 'Update':
                    # when multiple arms and events, need to specify both
                    mock_log['action'] = f'{self.action} record {self.patient_name} ({self.event_label} (Arm {self.arm_num}: {self.arm_name})'
                elif self.action == 'Delete':            
                    # when deleting, only arms need to be specified
                    mock_log['action'] = f'{self.action} record {self.patient_name} (Arm {self.arm_num}: {self.arm_name})'

        else:
            # non-longitudinal actions
            mock_log['action'] = f'{self.action} record {self.patient_name}'


        # details
        if self.action == 'Delete':
            mock_log['details'] = f"record_id = '{self.patient_name}'"
        else:
            details = ', '.join([f"{field['redcap_variable']} = '{field['value']}'" for field in self.fields])
            if self.instance and int(self.instance) > 1:
                details = f'[instance] = {self.instance}, ' + details
            mock_log['details'] = details

        return mock_log

    # --------------------------------------------------------------------------
    def create_mock_record(self):
        """
        Create a mock record based on log_info and proj_config.
        
        Inputs:
        --------    
        log_info: dict
            Dictionary containing patient_name, instrument_name, action, fields, verified, deleted.
        proj_config: dict
            Dictionary containing configurations like instance, num_of_arms, arm_num, arm_name, event_name, num_of_events.
        """

        if self.action == 'Delete':
            # if action is delete, return empty record
            return []


        mock_record = {'record_id': self.patient_name}
        record_fields = {field['redcap_variable']: field['value'] for field in self.fields}
        mock_record.update(record_fields)
        
        if self.instance:
            mock_record['redcap_repeat_instrument'] = self.instrument_name
            mock_record['redcap_repeat_instance'] = self.instance

        # standard redcap complete field
        if f'{self.instrument_name}_completed' in record_fields:
            mock_record[f'{self.instrument_name}_completed'] = record_fields[f'{self.instrument_name}_completed']
        else:
            mock_record[f'{self.instrument_name}_completed'] = '0'

        # -- longitudinal considerations --
        # if two arms, then there absolutely are multiple events
        # if only one arm, there can still be multiple events
        if "is_longitudinal" in self.proj_config:
            if self.num_of_arms > 1 or self.num_of_events > 1:
                mock_record['redcap_event_name'] = self.redcap_event_name

        return mock_record

    # --------------------------------------------------------------------------
    def make_db_format_record(self):

        record_fields = {field['redcap_variable']: field['value'] for field in self.fields}

        mock_db_crf = pd.DataFrame({
            'crf_name' : [self.instrument_name],
            'arm_num' : [self.arm_num],
            'unique_event_name' : [self.redcap_event_name],
            'instance' : [self.instance],
            'verified' : [self.verified],
            'deleted' : [self.deleted]
        })
        
        if self.deleted:
            mock_db_crf_data = pd.DataFrame(columns=['value', 'redcap_variable'])
        else:
            mock_db_crf_data = pd.DataFrame({
                'value' : record_fields.values(),
                'redcap_variable' : record_fields.keys()
            })

        mock_db_patients = pd.DataFrame({
            'patient_name' : [self.patient_name]
        })

        return {'crf_redcap' : mock_db_crf, 
                'crf_data_redcap' : mock_db_crf_data, 
                'patients' :  mock_db_patients}