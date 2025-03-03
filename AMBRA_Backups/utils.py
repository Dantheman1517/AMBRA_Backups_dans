from sys import platform
from pathlib import Path
from typing import Literal, Union
from redcap import Project
import zipfile
import logging
import subprocess
import os
import shutil
import pandas as pd
import hashlib
from AMBRA_Backups.REDCap_Log.redcap_log import REDCapLog
from AMBRA_Backups.Database.database import Database
from AMBRA_Utils.Study import Study


# ------------------------------------------------------------------------------
def format_error(msg: str, resolution: str = ""):
    """
    Raises error with specified message with nice formatting for
    easier debugging on Airflow. Example:
    ```
    #########################
    #
    #   Details     : The REDCap's project name and the name in the DB are different
    #   Resolution  : Harmonize the two names
    #
    #########################
    ```
    Resolution message is optional.

    Inputs:
    --------
    msg (str):
        Details about the error.

    exception_resolution (str):
        Suggestion on how to resolve the error.
        Defaults to empty string.
    """
    if resolution:
        raise_txt = f"""
        ########################
        # 
        #   Details     : {msg}
        #   Resolution  : {resolution}
        # 
        ########################
        """
    else:
        raise_txt = f"""
        ########################
        # 
        #   Details     : {msg}
        # 
        ########################
        """

    raise Exception(raise_txt)


# ------------------------------------------------------------------------------
def log_to_db(
    db: Database,
    src: Union[Study, REDCapLog, Project],
    level: Literal["INFO", "WARNING", "ERROR"],
    msg: str,
    resolution: str = "",
):
    """
    Logs the event to database of trial into `airflow_logs` table.

    Inputs:
    --------
    db (Database):
        Database of the trial.

    src (Union[Study, REDCapLog]):
        Source where the log is referring to:
        `Study`:        An Inteleshare study
        `REDCapLog`:    A REDCap log.
        `Project`:      A REDCap project.

    level (Literal['WARNING', 'ERROR']):
        `INFO`:     General useful information that most likely does not warrant action items.
        `WARNING`:  An oddity that might be an actionable item.
        `ERROR`:    Anything that warrants stopping the task immediately.

    msg (str):
        Description about the event.

    resolution (str):
        Instructions on suggestions of how to resolve the error.
        Defaults to empty string.

    Raises:
    --------
    Exception:
        When the level is `ERROR`.

    Returns:
    --------
    None
    """

    # Raise error if airflow_logs table not in schema
    if ("airflow_logs",) not in db.list_tables():
        format_error(
            f"Table airflow_logs is not in schema {db.db_name}.",
            "Create the airflow_logs table.",
        )

    # Handle src based on its type
    if type(src) is Study:
        db_msg = f"""
        Subject ID:     {src.patient_name}\n
        Study UUID:     {src.study_uid.replace(".", "_")}\n
        Details:        {msg}
        """
    elif type(src) is REDCapLog:
        db_msg = f"""
        Subject ID:     {src.patient_name}\n
        Log Timestamp:  {src.timestamp}\n
        Details:        {msg}
        """
    elif type(src) is Project:
        db_msg = f"""
        Project Title:  {src.export_project_info()["project_title"]}
        """
    # Insert log into airflow_logs table
    if resolution:
        db_msg = (
            db_msg
            + f"""\n
        Resolution:     {resolution}\n
        """
        )

    db.run_insert_query(
        """
        INSERT INTO airflow_logs (message, type)
        VALUES (%s, %s)
        """,
        (db_msg, level),
    )

    if level == "ERROR":
        format_error(msg, resolution)


# ------------------------------------------------------------------------------
def hash_file(file_path):
    """
    Returns the md5 hash of the file at file_path.
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise Exception("Only files can be hashed.")

    hasher = hashlib.md5()
    with open(file_path, "rb") as fopen:
        buf = fopen.read()
        hasher.update(buf)

    return hasher.hexdigest()


# ------------------------------------------------------------------------------
def extract(zip_file):
    """
    Extracts contents of the zip_file and places them into a directory with the
    same name.
    """
    zip_file = Path(zip_file)
    assert zip_file.exists()

    extraction_directory = zip_file.parent.joinpath(zip_file.stem)
    if extraction_directory.exists():
        logging.warning(
            f"Extracted directory {extraction_directory} already exists. Extraction skipped."
        )
    else:
        logging.info(f"Extracting zip file to {extraction_directory}")
        with zipfile.ZipFile(zip_file, "r") as zip:
            zip.extractall(path=extraction_directory)

    return extraction_directory


# ------------------------------------------------------------------------------
def convert_nifti(dicom_directory, output_directory):
    """
    Passes the dicom_directory to dcm2niix and outputs the nifti, bids and other
    files to the output_directory path.
    """
    if platform == "linux" or platform == "linux2":
        dcm2nii_path = Path(__file__).parent.parent.joinpath(
            "ExternalPrograms", "dcm2niix_linux"
        )
    elif platform == "darwin":
        dcm2nii_path = Path(__file__).parent.parent.joinpath(
            "ExternalPrograms", "dcm2niix"
        )

    if not dcm2nii_path.exists():
        raise Exception(f"Could not locate dcm2nii at {dcm2nii_path}")

    output_directory = Path(output_directory)
    if not output_directory.exists():
        os.makedirs(output_directory)

    dcm2nii = [
        str(dcm2nii_path),
        "-b",
        "y",
        "-f",
        "%d_%z_%s_%j",
        "-z",
        "y",
        "-o",
        str(output_directory),
        str(dicom_directory),
    ]

    subprocess.call(dcm2nii)


# ------------------------------------------------------------------------------
def extract_and_convert(zip_file, output_directory, cleanup=False):
    """
    Extracts dicoms from the zip_file and converts them to nifti using dcm2nii.

    Files are extracted into a directory with the same name as the zip_file.
    The nifti files are placed into this directory as well and the extracted dicoms
    are deleted after conversion.

    cleanup: bool
        If True, the extracted data and directory will be deleted after nifti conversion.
    """
    extraction_directory = extract(zip_file)
    convert_nifti(extraction_directory, output_directory)

    if extraction_directory.exists() and cleanup:
        logging.info(f"Removing {extraction_directory}.")
        shutil.rmtree(extraction_directory)


# ------------------------------------------------------------------------------
def html_to_dataframe(html):
    """
    Extract the CRF from an html table format and export as a pandas dataframe.

    html: html as a string or a file path.
    """
    # reports_df will be a list of dataframes, one for each table in the html.
    reports_df = pd.read_html(html)

    report_df = pd.DataFrame()
    for report in reports_df:
        report = report[[0, 1, 3]].T
        ## XXX: Not sure if this is the right approach yet - I may not want to transpose
        # I also may want to add in the table name as an additional row/column
        ## XXX: Merge into report_df

    return report_df


# ------------------------------------------------------------------------------
def strip_ext(input):
    """
    Removes the suffix from .nii and .nii.gz files and returns the stem.
    """
    stem = Path(input.name)
    suffix = stem.suffix
    if suffix == ".gz":
        stem = stem.with_suffix("")
        suffix = stem.suffix

    assert stem.suffix == ".nii"

    return stem.with_suffix("")


# ------------------------------------------------------------------------------
def df_to_db_table(db, df, table_name):
    """
    inputs df rows into table. Table must exist and have the same columns as df
    Null entries to the table should be filled with None in the df
    """

    # if table not not in db, error
    if table_name not in [table[0] for table in db.run_select_query("SHOW TABLES")]:
        raise ValueError(f"Table {table_name} not in database")

    # all df's columns must be in table
    table_columns = [
        col[0]
        for col in db.run_select_query(f"SHOW COLUMNS FROM {table_name}")
        if col[0] != "id"
    ]
    if not set(df.columns) <= set(table_columns):
        raise ValueError(f"""Columns in dataframe not in table {table_name}:
                         \ndf columns: \n{df.columns.to_list()}\n table columns: \n{table_columns}""")

    # Change 6/28/24: Think it would make sense to allow single quotes into the db
    #                 Wouldnt want to handle strings with single quotes in them later
    # if any single quotes, must have been handled before passed to function
    # if df.applymap(lambda x: isinstance(x, str) and "'" in x and "\\'" not in x).any().any():
    #     raise ValueError('Dataframe contains single quotes. Please remove them before inserting into database.')

    columns = df.columns.tolist()
    columns = "(" + ", ".join(columns) + ")"
    values_string = ", ".join(
        ["(" + ",".join(["%s"] * len(df.columns)) + ")"] * len(df)
    )
    update_string = ", ".join(
        [f"{column}=VALUES({column})" for column in df.columns[1:]]
    )
    values = df.values.tolist()
    values = [item for sublist in values for item in sublist]

    ret = db.run_insert_query(
        f"""INSERT INTO {table_name} 
                                      {columns} 
                                  VALUES 
                                      {values_string}
                                  ON DUPLICATE KEY UPDATE 
                                      {update_string}""",
        values,
    )

    return ret
