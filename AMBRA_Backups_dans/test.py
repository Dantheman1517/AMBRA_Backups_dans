

from datetime import datetime
import pandas as pd
import AMBRA_Backups_dans


db = AMBRA_Backups_dans.database.Database('test_db')
db.run_insert_query("""DELETE FROM patients""", [])
db.run_insert_query("""DELETE FROM CRF_RedCap""", [])
db.run_insert_query("""DELETE FROM CRF_Data_RedCap""", [])

project = AMBRA_Backups_dans.redcap_funcs.get_redcap_project('Dans test project')
AMBRA_Backups_dans.redcap_funcs.project_data_to_db(db, project, start_date=datetime(2025, 8, 5, 11, 19))


crf_redcap_table = pd.DataFrame(db.run_select_query("""SELECT patient_name, crf_name, instance, verified, deleted 
                                                       FROM CRF_RedCap
                                                       JOIN patients
                                                           ON patients.id = id_patient""", column_names=True))

expected_crf_row = pd.DataFrame({'patient_name': ['1'],
              'crf_name' : ['all_fields'],
              'instance' : [None],
              'verified' : [0],
              'deleted' : [0]})

assert crf_redcap_table.equals(expected_crf_row)
