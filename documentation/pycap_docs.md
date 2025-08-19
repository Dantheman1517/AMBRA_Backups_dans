# PyCap Functions and Examples

*Reference for PyCap API functions with practical examples*

### Basic Setup

```python
from redcap import Project

api_url = 'https://redcap.example.edu/api/'
api_key = 'SomeSuperSecretAPIKeyThatNobodyElseShouldHave'
project = Project(api_url, api_key)
```

### Export All Data

```python
data = project.export_records()
```

### Import Data

```python
to_import = [{'record': 'foo', 'test_score': 'bar'}]
response = project.import_records(to_import)
```

### File Operations

#### Import a File

```python
fname = 'something_to_upload.txt'
with open(fname, 'r') as fobj:
    project.import_file('1', 'file', fname, fobj)
```

#### Export a File

```python
content, headers = project.export_file('1', 'file')
with open(headers['name'], 'wb') as fobj:
    fobj.write(content)
```

#### Delete a File

```python
try:
    project.delete_file('1', 'file')
except redcap.RedcapError:
    # Throws this if file wasn't successfully deleted
    pass
except ValueError:
    # You screwed up and gave it a bad field name, etc
    pass
```

### Export PDF

Export a PDF file of all instruments (blank):

```python
content, _headers = project.export_pdf()
with open('all_instruments_blank.pdf', 'wb') as fobj:
    fobj.write(content)
```

## API Functions

### Project Information
- `export_project_info()` - Get project settings and information
- `export_version()` - Get REDCap version
- `export_project_xml()` - Export project as XML

### Data Operations
- `export_records()` - Export data records
- `import_records()` - Import data records
- `delete_records()` - Delete data records
- `export_metadata()` - Export data dictionary
- `import_metadata()` - Import data dictionary

### Arms and Events (Longitudinal Studies)
- `export_arms()` - Export study arms
- `import_arms()` - Import study arms
- `delete_arms()` - Delete study arms
- `export_events()` - Export events
- `import_events()` - Import events
- `delete_events()` - Delete events

### File Operations
- `export_file()` - Download a file
- `import_file()` - Upload a file
- `delete_file()` - Delete a file

### User Management
- `export_users()` - Export user list
- `import_users()` - Import users
- `export_user_roles()` - Export user roles
- `import_user_roles()` - Import user roles

### Logging and Auditing
- `export_logging()` - Export audit/logging information

### Reports and Surveys
- `export_reports()` - Export custom reports
- `export_survey_link()` - Get survey links
- `export_survey_participant_list()` - Get participant lists

## Error Handling

PyCap provides specific exception types for different error conditions:

```python
import redcap

try:
    # Your PyCap operations here
    pass
except redcap.RedcapError as e:
    # REDCap-specific errors (API errors, authentication, etc.)
    print(f"REDCap Error: {e}")
except ValueError as e:
    # Invalid parameters or data format errors
    print(f"Value Error: {e}")
except Exception as e:
    # Other unexpected errors
    print(f"Unexpected Error: {e}")
```

## Examples

### Automated Data Exports
```python
import pandas as pd
from redcap import Project

# Export data as pandas DataFrame
project = Project(api_url, api_key)
df = project.export_records(format_type='df')
```

### Bulk Data Import
```python
# Import multiple records
records_to_import = [
    {'record_id': '1', 'field1': 'value1', 'field2': 'value2'},
    {'record_id': '2', 'field1': 'value3', 'field2': 'value4'},
]
response = project.import_records(records_to_import)
```

### Project Metadata Management
```python
# Export data dictionary
metadata = project.export_metadata()

# Modify metadata programmatically
# ... your metadata modifications ...

# Import updated metadata
project.import_metadata(modified_metadata)
```

---

*Generated from PyCap documentation at: https://redcap-tools.github.io/PyCap/*  
*Last updated: 2025-01-08*
