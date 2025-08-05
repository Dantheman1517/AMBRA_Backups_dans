import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from tqdm import tqdm
from bs4 import BeautifulSoup
from redcap import Project
import configparser
import json
import numpy as np

from AMBRA_Backups import utils
from AMBRA_Backups.REDCap_Log.redcap_log import REDCapLog
import AMBRA_Backups
from AMBRA_Backups.utils import log_to_db


def get_config(config_path=None):
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path.home().joinpath(".redcap.cfg")
    if not config_file.exists():
        logging.error(f"Could not find credentials file: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    return config


def get_redcap_project(proj_name, config_path=None) -> Project:
    config = get_config(config_path=config_path)
    proj_config = config[proj_name]
    return Project("https://redcap.research.cchmc.org/api/", proj_config["token"])


def backup_project(project_name, output_dir, bckp_files=True):
    """
    Backup a REDCap project by exporting project information, metadata, records, users, roles, role assignments,
    files, and repeating instruments to specified output directory.

    Args:
        project_name (str): The name of the REDCap project.
        url (str): The URL of the REDCap project.
        api_key (str): The API key for accessing the REDCap project.
        output_dir (Path): The directory where the backup files will be saved.
        bckp_files (bool): If true, will download attached files.

    Returns:
        None
    """
    project = get_redcap_project(project_name)

    # Info
    # ---------------
    info_out = output_dir.joinpath(f"{project_name}_info.json")
    info_json = {
        "Project Name": project_name,
        "RedCap version": str(project.export_version()),
        "Backup date": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
    }
    with open(info_out, "w", encoding="utf-8") as f:
        json.dump(info_json, f, ensure_ascii=False, indent=4)

    # Data Dictionary
    # ---------------
    meta_json = project.export_metadata(format_type="json")
    meta_out = output_dir.joinpath(f"{project_name}_metadata.json")
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta_json, f, ensure_ascii=False, indent=4)

    # Data
    # ---------------
    forms_json = project.export_records(format_type="json")
    forms_out = output_dir.joinpath(f"{project_name}_forms.json")
    with open(forms_out, "w", encoding="utf-8") as f:
        json.dump(forms_json, f, ensure_ascii=False, indent=4)

    # Users
    # ---------------
    users_json = project.export_users(format_type="json")
    users_out = output_dir.joinpath(f"{project_name}_users.json")
    with open(users_out, "w", encoding="utf-8") as f:
        json.dump(users_json, f, ensure_ascii=False, indent=4)

    # User roles
    # ---------------
    roles_json = project.export_user_roles(format_type="json")
    roles_out = output_dir.joinpath(f"{project_name}_roles.json")
    with open(roles_out, "w", encoding="utf-8") as f:
        json.dump(roles_json, f, ensure_ascii=False, indent=4)

    role_assignment_json = project.export_user_role_assignment(format_type="json")
    role_assignment_out = output_dir.joinpath(f"{project_name}_roles_assignment.json")
    with open(role_assignment_out, "w", encoding="utf-8") as f:
        json.dump(role_assignment_json, f, ensure_ascii=False, indent=4)

    # Form-event mappings
    # fem = project.export_fem()

    # Files
    # ---------------
    if bckp_files:
        files_dir = output_dir.joinpath(f"{project_name}_Files")
        if not files_dir.exists():
            files_dir.mkdir()

        meta_df = pd.DataFrame(meta_json)

        # Find fields containing files
        files = meta_df[meta_df["field_type"] == "file"]

        for file_field_name in files["field_name"].values:
            these_records = project.export_records(fields=[file_field_name])
            for record in these_records:
                if record[file_field_name] != "":
                    content, headers = project.export_file(
                        record["record_id"],
                        file_field_name,
                        event=record.get("redcap_event_name"),
                        repeat_instance=record.get("redcap_repeat_instrument"),
                    )
                    file_path = files_dir.joinpath(
                        f"{record['record_id']} - {headers['name']}"
                    )
                    if not file_path.exists():
                        with open(file_path, "wb") as fobj:
                            fobj.write(content)

    # Repeating instruments
    # ---------------
    try:
        repeating_json = project.export_repeating_instruments_events(format_type="json")
        repeating_out = output_dir.joinpath(f"{project_name}_repeating.json")
        with open(repeating_out, "w", encoding="utf-8") as f:
            json.dump(repeating_json, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def get_project_schema(project_name, form):
    """
    returns a ready to insert dataframe of the schema of a redcap project into CRF_RedCap_Schema
    """

    # gathering
    project = get_redcap_project(project_name)
    df = pd.DataFrame(project.export_metadata())
    df = df[df["form_name"] == form]
    field_names = pd.DataFrame(project.export_field_names())
    field_names.rename(columns={"original_field_name": "field_name"}, inplace=True)
    df = pd.merge(field_names, df, on="field_name")

    # replacing
    def val_to_text(row):
        if row["field_type"] == "checkbox":
            dic = {
                op.split(",")[0].strip(): op.split(",")[1].strip()
                for op in row["select_choices_or_calculations"].split("|")
            }
            return dic[row["choice_value"]]
        else:
            return row["select_choices_or_calculations"]

    df["select_choices_or_calculations"] = df.apply(val_to_text, axis=1)

    def replace_seperators(row):
        if row["field_type"] == "radio":
            return row["select_choices_or_calculations"].replace(",", "=")
        else:
            return row["select_choices_or_calculations"]

    df["select_choices_or_calculations"] = df.apply(replace_seperators, axis=1)

    df.loc[
        (df["field_type"] == "checkbox")
        | (df["field_type"] == "radio")
        | (df["field_type"] == "yesno"),
        "data_type",
    ] = "int"
    df.loc[df["field_type"] == "text", "data_type"] = "string"

    df.loc[df["export_field_name"].str.contains("___"), "export_field_name"] = (
        df["export_field_name"] + ")"
    )
    df.loc[df["export_field_name"].str.contains("___"), "export_field_name"] = df[
        "export_field_name"
    ].str.replace("___", "(")
    df["redcap_variable"] = df["export_field_name"]

    # This question_order functionality is only approximate. Should be double checked after schena insertion
    df["question_order"] = df["export_field_name"].str.extract(r"(\d+)")

    def apply_decimals(group):
        i = 0
        for idx, row in group.iterrows():
            group.at[idx, "question_order"] = row["question_order"] + f".{(i + 1):02}"
            i += 1
        return group

    df.loc[
        (df["field_type"] == "checkbox") & (df["redcap_variable"].str.startswith("q")),
        "question_order",
    ] = (
        df[
            (df["field_type"] == "checkbox")
            & (df["redcap_variable"].str.startswith("q"))
        ]
        .groupby("question_order")
        .apply(apply_decimals)
        .reset_index(level=0, drop=True)["question_order"]
    )

    # truncating and renaming
    df = df[
        [
            "form_name",
            "redcap_variable",
            "export_field_name",
            "field_label",
            "select_choices_or_calculations",
            "field_type",
            "data_type",
            "question_order",
        ]
    ]
    df.rename(
        columns={
            "form_name": "crf_name",
            "export_field_name": "data_id",
            "select_choices_or_calculations": "data_labels",
            "field_label": "question_text",
            "field_type": "question_type",
        },
        inplace=True,
    )
    df.replace({"": None, np.nan: None}, inplace=True)
    return df


def comp_schema_cap_db(db_name, project_name):
    """
    Checks for differences between
        1. data table unique redcap_variables and schema's redcap_variables
        2. question_text in live redcap and db schema
        3. radio button options in live redcap and db schema
    Any differences are added as an error string to be thrown at the start
    of a dag making a report depending on the db schema(right now just csv reports 8/19/24)
    """

    db = AMBRA_Backups.database.Database(db_name)
    project = get_redcap_project(project_name)

    forms = [f["instrument_name"] for f in project.export_instruments()]

    master_discreps = ""

    for crf_name in forms:
        # redcap_variable discrepancies
        unique_data_vars = pd.DataFrame(
            db.run_select_query(
                """SELECT DISTINCT(redcap_variable) 
            FROM CRF_RedCap
            JOIN CRF_Data_RedCap
                ON CRF_RedCap.id = CRF_Data_RedCap.id_crf
            WHERE crf_name = %s""",
                [crf_name],
                column_names=True,
            )
        )
        var_discrep_string = ""
        if not unique_data_vars.empty:
            unique_data_vars = unique_data_vars["redcap_variable"]
            schema_vars = pd.DataFrame(
                db.run_select_query(
                    """SELECT redcap_variable FROM CRF_Schema_RedCap
                WHERE crf_name = %s""",
                    [crf_name],
                    column_names=True,
                )
            )["redcap_variable"]

            var_discreps = unique_data_vars[
                ~unique_data_vars.isin(schema_vars)
            ].to_list()
            if var_discreps:
                # redcap_variables inside the data table might not have a schema variable to coorispond to, but might have an active crf_id
                # So the non-included redcap_variable will be attached to a csv report if not taken out of the data table, or have the schema corrected. Case by case
                var_discrep_string = f"\nThe following CRF_Data_RedCap.redcap_variable's are not in CRF_schema_RedCap.redcap_variable's:\n{var_discreps}\n\n"

        # print('redcap_variables')
        # print('CRF_Data_RedCap')
        # display(unique_data_vars)
        # print('CRF_Schema_RedCap')
        # display(schema_vars)

        # question text discrepancies
        schema_questions = pd.DataFrame(
            db.run_select_query(
                """SELECT question_text, redcap_variable FROM CRF_Schema_RedCap
                                        WHERE crf_name = %s AND question_text IS NOT NULL""",
                [crf_name],
                column_names=True,
            )
        )
        schema_questions["variable-value"] = (
            schema_questions["redcap_variable"] + schema_questions["question_text"]
        )

        api_questions = pd.DataFrame(project.export_metadata())
        api_questions = api_questions[api_questions["form_name"] == crf_name]
        field_names = pd.DataFrame(project.export_field_names())
        field_names.rename(columns={"original_field_name": "field_name"}, inplace=True)
        api_questions = pd.merge(
            api_questions, field_names, on="field_name", how="left"
        )
        api_questions.loc[
            api_questions["export_field_name"].str.contains("___", na=False),
            "export_field_name",
        ] = api_questions.loc[
            api_questions["export_field_name"].str.contains("___", na=False),
            "export_field_name",
        ].apply(lambda x: x.split("___")[0] + "(" + x.split("___")[1] + ")")
        api_questions["redcap_variable"] = api_questions["export_field_name"]

        def only_html(row):
            soup = BeautifulSoup(row["field_label"], "html.parser")
            if bool(soup.find()):
                return row["field_label"]

        master_html = "".join(
            api_questions.apply(only_html, axis=1).dropna().values.tolist()
        )
        api_questions = api_questions[
            (api_questions["field_type"] != "descriptive")
            & ~(api_questions["field_label"].str.contains("record", case=False))
            & (~api_questions["field_name"].apply(lambda x: x in master_html))
        ][["redcap_variable", "field_label"]]
        api_questions["variable-value"] = (
            api_questions["redcap_variable"] + api_questions["field_label"]
        )

        question_discreps = api_questions[
            ~api_questions["variable-value"].isin(schema_questions["variable-value"])
        ]
        ques_discrep_string = ""
        if not question_discreps.empty:
            discrep_dict = {v[0]: v[1] for v in question_discreps.values}
            ques_discrep_string = f"\nThe following api-metadata question_text's are not in CRF_Schema_RedCap.question_text's:\n{{redcap_variable : question_text}}\n\n{discrep_dict}\n\n"

        # print('question_text')
        # print('schema_questions')
        # display(schema_questions)
        # print('api_questions')
        # display(api_questions.reset_index())

        # radio button option discrepancies
        schema_radio_options = pd.DataFrame(
            db.run_select_query(
                """SELECT * FROM CRF_Schema_RedCap
                                    WHERE crf_name = %s AND question_type = 'radio'""",
                [crf_name],
                column_names=True,
            )
        )
        radio_discrep_string = ""
        if not schema_radio_options.empty:
            schema_radio_options = schema_radio_options["data_labels"]

            def schema_rep_seps(string_ops):
                return "|".join(
                    [
                        ss.split("=")[0].strip()
                        + "="
                        + "=".join(ss.split("=")[1:]).strip()
                        for ss in string_ops.split("|")
                    ]
                )

            schema_radio_options = schema_radio_options.apply(schema_rep_seps)

            api_radio_options = pd.DataFrame(project.metadata)
            api_radio_options = api_radio_options[
                (api_radio_options["form_name"] == crf_name)
                & (api_radio_options["field_type"] == "radio")
            ][["field_name", "select_choices_or_calculations"]]

            def api_rep_seps(string_ops):
                return "|".join(
                    [
                        ss.split(",")[0].strip()
                        + "="
                        + ",".join(ss.split(",")[1:]).strip()
                        for ss in string_ops.split("|")
                    ]
                )

            api_radio_options["select_choices_or_calculations"] = api_radio_options[
                "select_choices_or_calculations"
            ].apply(api_rep_seps)

            radio_discreps = api_radio_options[
                ~api_radio_options["select_choices_or_calculations"].isin(
                    schema_radio_options
                )
            ]
            if not radio_discreps.empty:
                discrep_dict = {v[0]: v[1] for v in radio_discreps.values}
                radio_discrep_string = f"The following api-metadata radio button options's are not in CRF_Schema_RedCap.data_labels's(radio button options):\n{{redcap_variable : select_choices_or_calculations}}\n\n{discrep_dict}\n"

        # print('radio button options')
        # print('schema_radio_options')
        # display(schema_radio_options)
        # print('api_radio_options')
        # display(api_radio_options.reset_index()

        form_discrepancies = (
            var_discrep_string + ques_discrep_string + radio_discrep_string
        )
        if form_discrepancies:
            master_discreps += f"\n{crf_name:-^{40}}\n{form_discrepancies}"

    if master_discreps:
        print("====================================================================")
        print("====================================================================")
        print(master_discreps)
        print("====================================================================")
        print("====================================================================")
        raise Exception("Please handle the above discrepancies")


def grab_logs(db, project: Project, only_record_logs, start_date=None, end_date=None):
    """
    Extracts logs from redcap from start_date to end_date
    If only_record_logs is true only logs that modify records are extracted
    """
    if start_date is None:
        start_date = db.run_select_query("""SELECT * FROM backup_info_RedCap""")
        if (
            len(start_date) == 0
        ):  # if new project without any backup info, start from 2000, all data
            start_date = datetime(2000, 1, 1)
        else:
            start_date = start_date[0][1]
    if end_date is None:
        end_date = datetime.now()

    if not only_record_logs:
        logs = project.export_logging(begin_time=start_date, end_time=end_date)

    else:
        log_add = project.export_logging(
            begin_time=start_date,
            end_time=end_date,
            log_type="record_add",
        )
        log_edit = project.export_logging(
            begin_time=start_date,
            end_time=end_date,
            log_type="record_edit",
        )
        log_delete = project.export_logging(
            begin_time=start_date,
            end_time=end_date,
            log_type="record_delete",
        )

        logs = log_add + log_delete + log_edit
        logs.sort(key=lambda log: datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M"))

    return logs


def export_records_wrapper(
    db, project: Project, log: REDCapLog, patient_name, crf_name, instance
):
    """
    wrapper is necessary because of a export_record bug. If a repeating instance form is
    the first form in the project, a residual row is returned for other forms. This function excludes
    that residual.
    Also included an instance parameter
    """
    form_df = pd.DataFrame(
        project.export_records(records=[patient_name], forms=[crf_name])
    )

    if form_df.empty:
        return form_df

    form_df = form_df[form_df[crf_name + "_complete"] != ""]
    if instance:
        if "redcap_repeat_instrument" not in form_df.columns:
            log_to_db(
                db=db,
                src=log,
                level="WARNING",
                msg=f""""
                    Instance number {instance} was found for form {crf_name}, but there's no repeating instances in {crf_name}.

                    Potential reasons:
                    1. The instrument was repeating, but changed to non-repeating.
                      """,
            )
            # raise ValueError(f"""Project '{project.export_project_info()["project_title"]}' does not have repeat instances.
            #    \npatient_name: {patient_name}, crf_name: {crf_name}""")
        if instance not in form_df["redcap_repeat_instance"].to_list():
            log_to_db(
                db=db,
                src=log,
                level="WARNING",
                msg=f"""
                Instance number {instance} in form {crf_name} not of available instances: {form_df["redcap_repeat_instance"].to_list()}.

                Potential reasons:
                1. The instance was updated/created, but then deleted.

            """,
            )

            # raise ValueError(f"""Instance: {instance} not of available instances: {form_df["redcap_repeat_instance"].to_list()}
            #    \nIn project: {project.export_project_info()["project_title"]}, crf_name: {crf_name}, patient_name: {patient_name}""")
        form_df = form_df[form_df["redcap_repeat_instance"] == instance]
    return form_df


def check_project_name(db, project: Project):
    """
    Check if db's project name and REDCap's project name are the same. Insert
    into backup_info_RedCap if needed.

    Inputs:
    --------
    db (Database):
        Project's database

    project (Project):
        Project's REDCap
    """
    project_name = project.export_project_info()["project_title"].strip()
    db_backup_proj_name = db.run_select_query(
        "SELECT project_name FROM backup_info_RedCap"
    )

    if not db_backup_proj_name:
        db.run_insert_query(
            "INSERT INTO backup_info_RedCap (project_name) VALUES (%s)", [project_name]
        )
    elif len(db_backup_proj_name) > 1:
        poss_db_names = [name[0] for name in db_backup_proj_name]
        if project_name not in poss_db_names:
            raise ValueError(
                f"Live redcap name: {project_name}, is not in list of backup names: {poss_db_names}"
            )
    else:
        db_backup_proj_name = db_backup_proj_name[0][0]
        if project_name != db_backup_proj_name:
            raise ValueError(
                f"Live redcap name: {project_name}, database backup name: {db.db_name}.{db_backup_proj_name}"
            )


def get_project_instru_field_map(project: Project) -> dict:
    """
    Get dictionary of REDCap `project`'s instruments and its fields.

    Inputs:
    --------
    project (Project):
        REDCap project

    Returns:
    --------
    dict:
        Dictionary of instruments and fields mapping.
        Example:
            'Form 1': ['field1', 'field2']
    """
    instru_field_map = {}
    for var in project.metadata:
        field_name = var["field_name"]
        instru_name = var["form_name"]
        if field_name == "record_id":
            continue  # not necessary. record_id will be created at creation of a patient in redcap
        if instru_name not in instru_field_map:
            instru_field_map[instru_name] = []
        instru_field_map[instru_name].append(var["field_name"])

    for instru in instru_field_map:
        instru_field_map[instru].append(f"{instru}_complete")

    return instru_field_map


def get_repeating_instru(project: Project, instru_field_map: dict):
    """
    Get repeating instruments of REDCap `project`.

    Inputs:
    --------
    project (Project):
        REDCap Project.

    instru_field_map (dict)
        REDCap Project's instrument - field mapping.

    Returns:
    --------
    Set:
        Set of repeating forms
    """
    repeating_forms = set()
    if project.export_project_info()["has_repeating_instruments_or_events"] == 1:
        repeating_instru_events = [
            form["form_name"] for form in project.export_repeating_instruments_events()
        ]
        for name in instru_field_map:
            if name in repeating_instru_events:
                repeating_forms.add(name)

    return repeating_forms


def project_data_to_db(db, project: Project, start_date=None, end_date=None):
    """
    Exports data from redcap logs into db.
    Parses through REDCap logs to figure out which records have been changed.
    Then, check if these records still exist in the current REDCap state.
    If not, mark these as deleted in the db, if they are in the db,

    Inputs:
    --------
    db (Database):
        Database to insert data into.
    project (Project):
        REDCap project to extract data from.
    start_date (datetime, optional):
        Start date for log extraction. Defaults to None, which will use the last successful update time.
    end_date (datetime, optional):
        End date for log extraction. Defaults to None, which will use the current time.

    Algorithm:
    -------
    1. Extract logs from redcap from last successful update to now
    2. Insert new patients into db if any new patients
    3. Extract then remove instance, complete, and record_id from logs
    4. Find crf_name from log questions
    5. If log variables cannot match a crf_name, add to failed_to_add list,
       otherwise continue to handle crf
    6. If crf_row for (patient,crf_name,instance) does not exist, insert new crf_row
       if exists, update verified/complete if exists and differs from log
    7. Insert data into crf_data_redcap
    8. If any logs failed to add, raise error with failed_to_add list
    9. Update last export time in backup_info_RedCap

    Note: if a log appears in redcap, but not through the api, this is normal, the api
          just takes a few minutes
    """

    instru_field_map = get_project_instru_field_map(project)
    repeating_instru = get_repeating_instru(project, instru_field_map)

    # Grab record logs
    only_record_logs = True
    record_logs = grab_logs(db, project, only_record_logs, start_date, end_date)

    # Loop through record_logs and update db
    failed_to_add = []
    for i, log in tqdm(
        enumerate(record_logs), total=len(record_logs), desc="Adding data logs to db"
    ):
        if log["details"] == "":  # no changes to record
            continue

        log_instance = REDCapLog(
            project, log["action"], log["timestamp"], log["details"]
        )

        patient_name = log_instance.patient_name
        action = log_instance.get_action()

        patient_id = db.run_select_query(
            """SELECT id FROM patients WHERE patient_name = %s""", [patient_name]
        )

        # Check if there is a new patient
        if not patient_id:
            patient_id = db.run_insert_query(
                """INSERT INTO patients (patient_name, patient_id) VALUES (%s, %s)""",
                [patient_name, patient_name],
            )
        else:
            patient_id = patient_id[0][0]

        # Set subject to be deleted in db if log says delete
        if action == "DELETE":
            db.run_insert_query(
                """UPDATE CRF_RedCap SET deleted = 1 WHERE id_patient = %s""",
                [patient_id],
            )
            continue

        instance = log_instance.get_instance()
        crf_name = log_instance.get_crf_name(instru_field_map)

        if not crf_name:
            failed_to_add.append(log_instance)
            continue

        # If the log does not specify the instance and it is a repeating form, then instance = 1
        if (instance is None) and (crf_name in repeating_instru):
            instance = 1

        crf_row = pd.DataFrame(
            db.run_select_query(
                f"""SELECT * FROM CRF_RedCap WHERE id_patient = {patient_id} AND crf_name = \'{crf_name}\' 
                                    AND instance {"IS NULL" if instance is None else f"= {instance}"} AND deleted = '0'""",
                column_names=True,
            )
        )  # cant use run_select_query.record here, because ('IS NULL' or '= #') is not a valid sql variable

        # Get current state of REDCap data for patient_name
        record_df = export_records_wrapper(
            db=db,
            project=project,
            log=log_instance,
            patient_name=patient_name,
            crf_name=crf_name,
            instance=instance,
        )

        # Deleted record in redcap not in db
        if record_df.empty and crf_row.empty:
            continue

        # Deleted record in redcap in db
        elif record_df.empty and not crf_row.empty:
            deleted = 1
            db.run_insert_query(
                """UPDATE CRF_RedCap SET deleted = %s WHERE id = %s""",
                [deleted, str(crf_row["id"].iloc[0])],
            )

        # Data to enter
        elif not record_df.empty:
            # preprocess record_df for data insertion/update
            irrelevant_columns = {
                "redcap_repeat_instrument",
                "redcap_event_name",
                "redcap_repeat_instance",
            }
            record_df = record_df.drop(irrelevant_columns, axis=1, errors="ignore")
            record_df = record_df.melt(var_name="redcap_variable")
            record_df.loc[
                record_df["redcap_variable"].str.contains("___"), "redcap_variable"
            ] = record_df["redcap_variable"] + ")"
            record_df.loc[
                record_df["redcap_variable"].str.contains("___"), "redcap_variable"
            ] = record_df["redcap_variable"].str.replace("___", "(")

            if not crf_row.empty:  # update
                if f"{crf_name}_status" in record_df["redcap_variable"].to_list():
                    if (
                        record_df.loc[
                            record_df["redcap_variable"] == f"{crf_name}_status",
                            "value",
                        ].iloc[0]
                        == "4"
                        or record_df.loc[
                            record_df["redcap_variable"] == f"{crf_name}_status",
                            "value",
                        ].iloc[0]
                        == "5"
                    ):
                        verified = 1
                        db.run_insert_query(
                            """UPDATE CRF_RedCap SET verified = %s WHERE id = %s""",
                            [verified, str(crf_row["id"].iloc[0])],
                        )
                crf_id = crf_row["id"].iloc[0]
                record_df["id_crf"] = crf_id

                db_vars = db.run_select_query(
                    """SELECT redcap_variable FROM CRF_Data_RedCap WHERE id_crf = %s""",
                    [crf_id.item()],
                )
                db_vars = [v[0] for v in db_vars]
                for _, row in record_df.iterrows():
                    if row["redcap_variable"] in db_vars:
                        db.run_insert_query(
                            "UPDATE CRF_Data_RedCap SET value = %s WHERE id_crf = %s AND redcap_variable = %s",
                            [row["value"], crf_id.item(), row["redcap_variable"]],
                        )
                    else:
                        # this condition is from a previous method of inserting into the database only using logs.
                        # The new(current 10/30/24) method initializes data into the data table with every value, the logs only used fields that were filled out.
                        # after api initializations crf data, the data is only updated, not inserted. So existing crf data before this implementation will never
                        # have their new values inserted, thus this else condition inserts the missing data
                        db.run_insert_query(
                            """INSERT INTO CRF_Data_RedCap (id_crf, value, redcap_variable) VALUES (%s, %s, %s)""",
                            [crf_id.item(), row["value"], row["redcap_variable"]],
                        )

            elif crf_row.empty:  # insert
                deleted = 0
                verified = 0
                if f"{crf_name}_status" in record_df["redcap_variable"].to_list():
                    if (
                        record_df.loc[
                            record_df["redcap_variable"] == f"{crf_name}_status",
                            "value",
                        ].iloc[0]
                        == "4"
                        or record_df.loc[
                            record_df["redcap_variable"] == f"{crf_name}_status",
                            "value",
                        ].iloc[0]
                        == "5"
                    ):
                        verified = 1
                crf_id = db.run_insert_query(
                    """INSERT INTO CRF_RedCap (id_patient, crf_name, instance, deleted, verified)
                                    VALUES (%s, %s, %s, %s, %s)""",
                    [patient_id, crf_name, instance, deleted, verified],
                )
                record_df["id_crf"] = crf_id

                # insert record df rows into CRF_Data_RedCap
                utils.df_to_db_table(db, record_df, "CRF_Data_RedCap")

    # After trying to add all the logs, if there are any logs with questions not attached
    # to a current crf (outdated variable), they will be printed to an error string

    if failed_to_add:
        failed_to_add_str = """
        ##############\n
        #\t   Failed to add the following logs:\n
        #  
        """
        for log in failed_to_add:
            failed_to_add_str += f"""\n
            #\t   Patient:  {log.patient_name} \n
            #\t   Action:   {log.action} \n
            #\t   Details:  {log.details}  \n  
            #
            """
            log_to_db(
                db=db,
                src=log,
                level="WARNING",
                msg=f"""Could not find form that the variables belong to.
                All of the variables might be outdated.
                Variables: {log.variables}

                Potential reasons:
                1. The variables and the Instrument were both deleted.
                2. Only the variables' were deleted.
                3. The variables' names changed.""",
            )

        failed_to_add_str += "\n##############"
        logging.info(failed_to_add_str)

    # Update project backup info
    project_name = project.export_project_info()["project_title"].strip()
    db.run_insert_query(
        "UPDATE backup_info_RedCap SET last_backup = %s WHERE project_name = %s",
        [datetime.now(), project_name],
    )


# using main for testing purposes, manual backups
if __name__ == "__main__":  #
    import AMBRA_Backups

    testing = 0
    db_name = "CAPTIVA"
    project_name = "CAPTIVA DC"
    # db_name = 'SISTER'
    # project_name = '29423 Vagal - SISTER'
    if testing:
        db = AMBRA_Backups.database.Database("CAPTIVA_Test")
        project = get_redcap_project(
            "14102 Khandwala-Radiology Imaging Services Core Lab Workflow"
        )
    else:
        db = AMBRA_Backups.database.Database(db_name)
        project = get_redcap_project(project_name)
    date = datetime(2024, 12, 3)
    AMBRA_Backups.redcap_funcs.project_data_to_db(db, project)

    # manual backup
    # start_date = datetime(2023, 1, 1)
    # db.run_insert_query("""UPDATE backup_info_RedCap SET last_backup = %s""", [start_date])
    # start_date = datetime(2020, 7, 9, 11, 30)
    # end_date = datetime(2024, 7, 1, 13, 41)
    # project_data_to_db(db, project, start_date)

    # inserting logs only for select patient
    # project = AMBRA_Backups.redcap_funcs.get_redcap_project('CAPTIVA Data Collection')
    # logs = AMBRA_Backups.redcap_funcs.grab_logs(db, project, 1, start_date)
    # dates = []
    # for log in logs:
    #     if log['record'] == '1006':
    #         dates.append((datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M')+ timedelta(minutes=1), datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M') - timedelta(minutes=1)))

    # for date in dates:
    #     project_data_to_db(db, project, date[1], date[0])
