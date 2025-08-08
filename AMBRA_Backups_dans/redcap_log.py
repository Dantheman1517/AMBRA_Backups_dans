"""
02/25/2025: Class for REDCap log. Created as handling logs were getting complicated.
(ie. extracting details, putting the log into the Database)
"""

import re
from redcap import Project


################################################################################
class REDCapLog:
    # --------------------------------------------------------------------------
    def __init__(self, project: Project, action, timestamp: str, details: str):
        """
        Initialize REDCap log class. Each instance represent a log
        in the 'Logging' page of REDCap.

        Inputs:
        --------
        patient_name (str):
            The log's record ID.

        timestamp (str):
            The log's timestamp.

        details (str):
            The log's details string.
        """
        self.project = project
        self.patient_name = self._extract_patient_name(action)
        self.action = action
        self.timestamp = timestamp
        self.original_details = details
        self.details = self.extract_details()
        self.variables = list(self.details.keys())
        
        # Parse arm and event information for longitudinal projects
        self._parse_arm_event_info()

    # --------------------------------------------------------------------------
    def extract_details(self):
        """
        Extract a dictionary details from log['details']
        Example original log details:


        Algorithm: left right pointer
        - Left pointer indicates start of var, right pointer at end of var
        - Keep a list of stuff like quotes to keep in track the closing quotes
        - Right pointer must be at the ending quote (except when it's the ~checked~ case)
        - Set left pointer to be at next thing always

        Returns:
        --------
        dict:
            A dictionary of variables and values.
            Example:
            ```
            {
            '[instance]' : 2,
            'var01' : 'value01'
            }
            ```
        """
        details = self.original_details
        n = len(details)
        details_dict = dict()
        if n <= 1:
            return details_dict
        left = 0
        right = 1

        while right < n:
            # When current var is [instance = int]
            if details[left] == "[":
                check = details[left : left + 12]
                if check == "[instance = ":
                    substring = details[left:]
                    start = substring.index("= ") + 2 + left
                    end = substring.index("]") + left
                    details_dict["[instance]"] = int(details[start:end])
                    right = end + 1
                else:
                    raise Exception("This case should not be possible")

            # For regular variables
            else:
                # Extract variable
                substring = details[left:]
                end_var = substring.index(" = ") + left
                variable = details[left:end_var]

                # Find value attached to variable
                start_val = end_var + 3
                right = start_val + 1

                if details[start_val] == "'":
                    found_val = False
                    while not found_val:
                        if right == n:
                            found_val = True
                            continue
                        current_r = details[right]

                        # If found potential enclosing single quote
                        if current_r == "'":
                            # When at the end of string
                            if (right + 1) >= n:
                                found_val = True
                                continue
                            # Check if next character is a comma (eg `q1001 = '2', q1002 = '3'`)
                            next_chr = details[right + 1]
                            right += 1

                            # If comma and correct number of quotes so far, then assume enclosing quote
                            if next_chr == ",":
                                found_val = True
                                continue
                        # Else keep going
                        else:
                            right += 1

                # For cases like `q1003 = checked`
                else:
                    substring = details[start_val:]
                    if "," in substring:
                        right = substring.index(",") + start_val

                    # When at the end of details
                    else:
                        right = n

                val = details[start_val:right]
                details_dict[variable] = val

            left = right + 2
            right = left + 1

        return details_dict

    # --------------------------------------------------------------------------
    def get_instance(self):
        """
        Get instance of record in REDCap.

        Returns:
        --------
        int:
            Instance number of record.
        """
        details = self.details

        if "[instance]" in details:
            # If the log contains the instance number and nothing else, then
            # no other data was changed, thus rendering the instance info irrelevant
            if len(details) == 1:
                return None
            instance = details["[instance]"]
            return instance

        return None

    # --------------------------------------------------------------------------
    def get_crf_name(self, instru_field_map: dict):
        details = self.details
        crf_name = None

        for instru in instru_field_map:
            fields = instru_field_map[instru]
            for field in fields:
                regex = rf"^{field}(\([a-zA-z0-9]*\.?[a-zA-z0-9]*\))?$"  # Handles multi choice var

                for detail_var in details:
                    if re.fullmatch(regex, detail_var):
                        return instru

        self.crf_name = crf_name
        return crf_name

    # --------------------------------------------------------------------------
    def get_action(self):
        action = self.action.split(" ")[:-1]
        action = " ".join(action)
        if "Update record" in action:
            return "UPDATE"
        if "Delete record" in action:
            return "DELETE"
        if "Create record" in action:
            return "CREATE"

    # --------------------------------------------------------------------------
    def _parse_arm_event_info(self):
        """
        Parse arm and event information from action string for longitudinal projects.
        Implements logic for determining arm_name and event_name based on project structure.
        """
        try:
            # Check if project is longitudinal
            project_info = self.project.export_project_info()
            is_longitudinal = project_info.get('is_longitudinal', 0)
            
            if is_longitudinal:
                # Get arms
                arms = self.project.export_arms()
                
                if len(arms) > 1:
                    # Parse arm name from action
                    self.arm_name = self._parse_arm_from_action(arms)
                elif len(arms) == 1:
                    # Use the single arm's name
                    self.arm_name = arms[0].get('name', f"Arm {arms[0]['arm_num']}")
                else:
                    raise Exception('Project is longitudinal, but no arms. IMPOSSIBLE!!!')
                
                if 'delete' in self.action.lower():
                    # If the action is to delete, only the arm is needed to be specified
                    self.event_name = None
                else:
                    # Get events
                    events = self.project.export_events()
                    
                    if len(events) > 1:
                        # Parse event name from action
                        self.event_name = self._parse_event_from_action(events)
                    elif len(events) == 1:
                        # Use the single event's name
                        self.event_name = events[0].get('event_name')
                    else:
                        raise Exception('Project is longitudinal, but no events. IMPOSSIBLE!!!')
            else:
                self.arm_name = None
                self.event_name = None
                
        except Exception as e:
            # If there's any error in parsing, set defaults and continue
            print(f"Warning: Error parsing arm/event info: {e}")
            self.arm_name = None
            self.event_name = None
    
    # --------------------------------------------------------------------------
    def _parse_arm_from_action(self, arms):
        """
        Parse arm name from action string.
        Example: "Create record 1 (Event 1 (Arm 1: Arm 1))" -> "Arm 1"
        """
        # Look for pattern like "(Arm X: Arm Name)"
        arm_pattern = r'\(Arm (\d+): ([^)]+)\)'
        match = re.search(arm_pattern, self.action)
        
        if match:
            arm_num = int(match.group(1))
            arm_name = match.group(2)
            return arm_name
        
        # Fallback: try to find arm by number in parentheses
        for arm in arms:
            if f"Arm {arm['arm_num']}" in self.action:
                return arm.get('name', f"Arm {arm['arm_num']}")
        
        # Default to first arm if no match found
        return arms[0].get('name', f"Arm {arms[0]['arm_num']}")
    
    # --------------------------------------------------------------------------
    def _parse_event_from_action(self, events):
        """
        Parse event name from action string.
        Example: "Create record 1 (Event 1 (Arm 1: Arm 1))" -> "Event 1"
        """
        # Look for pattern like "(Event Name (Arm X: Arm Name))"
        event_pattern = r'\(([^(]+) \(Arm \d+:'
        match = re.search(event_pattern, self.action)
        
        if match:
            event_name = match.group(1).strip()
            return event_name
        
        # Fallback: look for any event name mentioned in action
        for event in events:
            if event['event_name'] in self.action:
                return event['event_name']
        
        # Default to first event if no match found
        return events[0].get('event_name')
    
    # --------------------------------------------------------------------------
    def _extract_patient_name(self, action):
        """
        Extract patient/record ID from action string.
        Example: "Create record 1 (Event 1 (Arm 1: Arm 1))" -> "1"
        """
        # Look for pattern like "record X" where X is the record ID
        record_pattern = r'record (\w+)'
        match = re.search(record_pattern, action)
        
        if match:
            return match.group(1)
        
        # Fallback to original method
        return action.split(" ")[-1].strip().rstrip(')')
