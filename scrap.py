from AMBRA_Backups_dans.redcap_funcs import get_redcap_project
from AMBRA_Backups_dans.redcap_log import REDCapLog

def test_redcap_log_parsing(project):
    """
    Test the REDCapLog parsing functionality with sample log entries.
    """
    print("\n=== Testing REDCapLog Arm/Event Parsing ===")
    
    # Test cases based on actual log entries we've seen
    test_cases = [
        {
            'action': 'Create record 1 (Event 1 (Arm 1: Arm 1))',
            'timestamp': '2025-03-24 11:57',
            'details': "form_1_complete = '0', record_id = '1'"
        },
        {
            'action': 'Update record 2 (Event1_Arm2 (Arm 2: Arm 2))',
            'timestamp': '2025-03-24 12:00',
            'details': "form_2_complete = '1', field1 = 'test'"
        },
        {
            'action': 'Delete record 3 (Event 1 (Arm 1: Arm 1))',
            'timestamp': '2025-03-24 12:15',
            'details': ""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Action: {test_case['action']}")
        
        try:
            # Create REDCapLog instance
            log = REDCapLog(
                project=project,
                action=test_case['action'],
                timestamp=test_case['timestamp'],
                details=test_case['details']
            )
            
            print(f"  Patient Name: {log.patient_name}")
            print(f"  Parsed Arm: {getattr(log, 'arm_name', 'Not set')}")
            print(f"  Parsed Event: {getattr(log, 'event_name', 'Not set')}")
            print(f"  Action Type: {log.get_action()}")
            
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    project = get_redcap_project('Dans test project')
    
    # Get project info
    project_info = project.export_project_info()
    print(f"Project title: {project_info['project_title']}")
    print(f"Is longitudinal: {project_info['is_longitudinal']}")
    
    # Test arms and events for longitudinal project
    print("\n=== Testing Arms and Events ===")
    
    is_longitudinal = project_info.get('is_longitudinal', 0)
    
    if is_longitudinal:
        # Test export_arms
        try:
            arms = project.export_arms()
            print(f"\nArms found: {len(arms)}")
            for i, arm in enumerate(arms):
                print(f"  Arm {i+1}: {arm}")
        except Exception as e:
            print(f"Error exporting arms: {e}")
        
        # Test export_events
        try:
            events = project.export_events()
            print(f"\nEvents found: {len(events)}")
            for i, event in enumerate(events):
                print(f"  Event {i+1}: {event}")
        except Exception as e:
            print(f"Error exporting events: {e}")
    else:
        print("Project is not longitudinal - no arms or events to check")
    
    # Test REDCapLog parsing
    test_redcap_log_parsing(project)
