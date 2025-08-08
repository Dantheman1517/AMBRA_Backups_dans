# Documentation References

This file contains links to important documentation and resources for the AMBRA_Backups_dans project.

## REDCap & PyCap Documentation

### PyCap - Python Interface for REDCap API
- **URL**: https://redcap-tools.github.io/PyCap/
- **Description**: Official documentation for PyCap, a Python interface to the REDCap Application Programming Interface (API)
- **Key Features**:
  - Minimal interface exposing all required and optional API parameters
  - Makes simple things easy & hard things possible
  - Compatible with pandas dataframes
  - MIT licensed

### Installation
```bash
# Install latest version
pip install PyCap

# Install with pandas support
pip install PyCap[all]

# Install bleeding edge from GitHub
pip install -e git+https://github.com/redcap-tools/PyCap.git#egg=PyCap
```

### Citation
If you use PyCap in your research, please cite:
```
Burns, S. S., Browne, A., Davis, G. N., Rimrodt, S. L., & Cutting, L. E. PyCap (Version 1.0) [Computer Software]. 
Nashville, TN: Vanderbilt University and Philadelphia, PA: Childrens Hospital of Philadelphia. 
Available from https://github.com/redcap-tools/PyCap. doi:10.5281/zenodo.9917
```

## API Reference Sections

The PyCap documentation includes comprehensive coverage of:

- **Project**: Core project functionality
- **Arms**: Study arms management
- **Data Access Groups**: DAG operations
- **Events**: Event management for longitudinal studies
- **Field Names**: Field name operations
- **File Repository**: File repository management
- **Files**: File upload/download operations
- **Instruments**: Survey instruments
- **Logging**: Project logging
- **Metadata**: Data dictionary operations
- **Project Info**: Project information
- **Repeating**: Repeating instruments and events
- **Records**: Data record operations
- **Reports**: Report generation
- **Surveys**: Survey management
- **Users**: User management
- **User Roles**: Role-based permissions
- **Version**: Version information

## Additional Resources

### REDCap Official Documentation
- **REDCap Consortium**: https://www.project-redcap.org/
- **REDCap API Documentation**: Available within your REDCap instance under "API"

### Related Tools
- **REDCap-Tools GitHub Organization**: https://github.com/redcap-tools/
- **PyCap GitHub Repository**: https://github.com/redcap-tools/PyCap

---

*Last Updated: 2025-01-08*
