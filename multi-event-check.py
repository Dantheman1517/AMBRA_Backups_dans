from AMBRA_Backups_dans.redcap_funcs import get_redcap_project

# Create a new REDCap project object
project_name = "Dans test project"  # Replace with your actual project name
project = get_redcap_project(project_name)

# Example usage:
project_info = project.export_project_info()
print(f"Project title: {project_info['project_title']}")
print(f"Project language: {project_info['project_language']}")
print(f"Is longitudinal: {project_info['is_longitudinal']}")

# Check for multiple events in the project
def check_multiple_events(project):
    """
    Check if the REDCap project has multiple events and display event information.
    """
    print("\n=== Event Analysis ===")
    
    # Check if project is longitudinal (has events)
    is_longitudinal = project_info.get('is_longitudinal', 0)
    
    if is_longitudinal == 0:
        print("This is a classic (non-longitudinal) project - no events to check.")
        return []
    
    # Export events if project is longitudinal
    try:
        events = project.export_events()
        print(f"Number of events found: {len(events)}")
        
        if len(events) > 1:
            print("\nMultiple events detected:")
            for i, event in enumerate(events, 1):
                print(f"  {i}. Event Name: '{event['event_name']}'")
                print(f"     Unique Event Name: '{event['unique_event_name']}'")
                print(f"     Arm Number: {event.get('arm_num', 'N/A')}")
                print(f"     Event ID: {event.get('event_id', 'N/A')}")
                print(f"     Custom Event Label: '{event.get('custom_event_label', '')}'")
                print()
        elif len(events) == 1:
            print("\nSingle event found:")
            event = events[0]
            print(f"  Event Name: '{event['event_name']}'")
            print(f"  Unique Event Name: '{event['unique_event_name']}'")
            print(f"  Arm Number: {event.get('arm_num', 'N/A')}")
            print(f"  Event ID: {event.get('event_id', 'N/A')}")
            print(f"  Custom Event Label: '{event.get('custom_event_label', '')}'")
        else:
            print("No events found despite longitudinal status.")
            
        return events
        
    except Exception as e:
        print(f"Error exporting events: {e}")
        return []

# Run the event check
events = check_multiple_events(project)

print("\n=== Additional Project Capabilities ===")
print("You can now use the project object to:")
print("- Export data: project.export_records()")
print("- Export metadata: project.export_metadata()")
print("- Export users: project.export_users()")
print("- Export events: project.export_events()")
print("- And much more...")
