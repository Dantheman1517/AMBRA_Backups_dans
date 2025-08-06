from datetime import datetime
import pandas as pd
import AMBRA_Backups_dans

# Debug script to understand what's happening with project_data_to_db

db = AMBRA_Backups_dans.database.Database('test_db')
db.run_insert_query("""DELETE FROM patients""", [])
db.run_insert_query("""DELETE FROM CRF_RedCap""", [])
db.run_insert_query("""DELETE FROM CRF_Data_RedCap""", [])

project = AMBRA_Backups_dans.redcap_funcs.get_redcap_project('Dans test project')

# Let's check what logs are being retrieved
print("=== DEBUGGING project_data_to_db ===")
record_logs = AMBRA_Backups_dans.redcap_funcs.grab_logs(db, project, True, start_date=datetime(2025, 8, 5, 16, 5))
print(f"Number of logs retrieved: {len(record_logs)}")
for i, log in enumerate(record_logs):
    print(f"Log {i}: {log}")
    print()

# Check instrument field mapping
instru_field_map = AMBRA_Backups_dans.redcap_funcs.get_project_instru_field_map(project)
print(f"Instrument field mapping: {instru_field_map}")
print()

# Check repeating instruments
repeating_instru = AMBRA_Backups_dans.redcap_funcs.get_repeating_instru(project, instru_field_map)
print(f"Repeating instruments: {repeating_instru}")
print()

# Process each log manually to see what's happening
if record_logs:
    log = record_logs[0]  # Process first log
    print(f"Processing log: {log}")
    
    log_instance = AMBRA_Backups_dans.redcap_log.REDCapLog(
        project, log["action"], log["timestamp"], log["details"]
    )
    
    print(f"Patient name: {log_instance.patient_name}")
    print(f"Action: {log_instance.get_action()}")
    print(f"Details: {log_instance.details}")
    print(f"Variables: {log_instance.variables}")
    print(f"Instance: {log_instance.get_instance()}")
    
    crf_name = log_instance.get_crf_name(instru_field_map)
    print(f"CRF name: {crf_name}")
    
    if crf_name:
        # Let's debug the export_records_wrapper step by step
        print(f"\n=== Debugging export_records_wrapper ===")
        
        # First, check what project.export_records returns directly
        raw_records = project.export_records(records=[log_instance.patient_name], forms=[crf_name])
        print(f"Raw export_records result:")
        raw_df = pd.DataFrame(raw_records)
        print(f"Shape: {raw_df.shape}")
        print(raw_df)
        
        if not raw_df.empty:
            complete_column = crf_name + "_complete"
            print(f"\nLooking for column: {complete_column}")
            print(f"Available columns: {raw_df.columns.tolist()}")
            
            if complete_column in raw_df.columns:
                print(f"Values in {complete_column}: {raw_df[complete_column].tolist()}")
                filtered_df = raw_df[raw_df[complete_column] != ""]
                print(f"After filtering != '': {filtered_df.shape}")
                print(filtered_df)
            else:
                print(f"Column {complete_column} not found!")
        
        # Now call the actual wrapper
        record_df = AMBRA_Backups_dans.redcap_funcs.export_records_wrapper(
            db=db,
            project=project,
            log=log_instance,
            patient_name=log_instance.patient_name,
            crf_name=crf_name,
            instance=log_instance.get_instance(),
        )
        print(f"\nWrapper result - Shape: {record_df.shape}")
        print(record_df)
    else:
        print("No CRF name found - this log would be added to failed_to_add")

print("\n=== Running project_data_to_db ===")
AMBRA_Backups_dans.redcap_funcs.project_data_to_db(db, project, start_date=datetime(2025, 8, 5, 11, 19))

print("\n=== Final database state ===")
# Check patients table
patients_table = pd.DataFrame(db.run_select_query("""SELECT id, patient_name, patient_id FROM patients"""))
print("Patients table:")
print(patients_table)

# Join with patients table like the test does
crf_redcap_table = pd.DataFrame(db.run_select_query("""SELECT patient_name, crf_name, instance, verified, deleted 
                                                       FROM CRF_RedCap
                                                       JOIN patients
                                                           ON patients.id = id_patient""", column_names=True))
print("\nCRF_RedCap table (joined with patients):")
print(crf_redcap_table)

# Also show the expected format
expected_crf_row = pd.DataFrame({'patient_name': ['1'],
              'crf_name' : ['all_fields'],
              'instance' : [None],
              'verified' : [0],
              'deleted' : [0]})
print("\nExpected:")
print(expected_crf_row)

print(f"\nComparison result: {crf_redcap_table.equals(expected_crf_row)}")
