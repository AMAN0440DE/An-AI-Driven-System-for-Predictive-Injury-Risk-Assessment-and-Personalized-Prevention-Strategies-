import os
import json
import pandas as pd
import datetime

# Create scenarios directory if it doesn't exist
def ensure_scenarios_dir():
    if not os.path.exists('scenarios'):
        os.makedirs('scenarios')

def save_scenario(name, data):
    """
    Saves a scenario to disk.
    
    Args:
        name: Name of the scenario
        data: Dictionary containing scenario data
    """
    ensure_scenarios_dir()
    
    # Generate a safe filename from the scenario name
    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    # Add timestamp for versioning
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{safe_name}_{timestamp}.json"
    
    # Save the data
    with open(os.path.join('scenarios', filename), 'w') as f:
        json.dump({
            'name': name,
            'data': data,
            'timestamp': timestamp
        }, f)
    
    return filename

def load_scenario():
    """
    Loads all saved scenarios.
    
    Returns:
        Dictionary containing all saved scenarios
    """
    ensure_scenarios_dir()
    scenarios = {}
    
    # Get all json files in the scenarios directory
    files = [f for f in os.listdir('scenarios') if f.endswith('.json')]
    
    # Group by scenario name (remove timestamp part)
    scenario_groups = {}
    
    for filename in files:
        try:
            with open(os.path.join('scenarios', filename), 'r') as f:
                scenario_data = json.load(f)
                name = scenario_data['name']
                timestamp = scenario_data.get('timestamp', '')
                
                if name not in scenario_groups:
                    scenario_groups[name] = []
                
                scenario_groups[name].append((timestamp, filename, scenario_data['data']))
        except Exception as e:
            print(f"Error loading scenario {filename}: {e}")
    
    # For each scenario, keep the latest version
    for name, versions in scenario_groups.items():
        # Sort by timestamp (descending)
        sorted_versions = sorted(versions, key=lambda x: x[0], reverse=True)
        # Keep the latest version
        if sorted_versions:
            scenarios[name] = sorted_versions[0][2]
    
    return scenarios

def load_all_scenarios():
    """
    Loads all saved scenarios from disk.
    
    Returns:
        Dictionary containing all saved scenarios
    """
    ensure_scenarios_dir()
    scenarios = {}
    
    # Get all json files in the scenarios directory
    files = [f for f in os.listdir('scenarios') if f.endswith('.json')]
    
    for filename in files:
        try:
            with open(os.path.join('scenarios', filename), 'r') as f:
                scenario_data = json.load(f)
                name = scenario_data['name']
                timestamp = scenario_data.get('timestamp', '')
                
                if name not in scenarios:
                    scenarios[name] = {}
                
                version_name = f"{name} ({timestamp})"
                scenarios[name][version_name] = scenario_data['data']
        except Exception as e:
            print(f"Error loading scenario {filename}: {e}")
    
    return scenarios

def delete_scenario(name):
    """
    Deletes a scenario from disk.
    
    Args:
        name: Name of the scenario to delete
    
    Returns:
        True if successful, False otherwise
    """
    ensure_scenarios_dir()
    
    # Get all json files in the scenarios directory
    files = [f for f in os.listdir('scenarios') if f.endswith('.json')]
    
    # Find files that match the scenario name
    deleted = False
    for filename in files:
        try:
            with open(os.path.join('scenarios', filename), 'r') as f:
                scenario_data = json.load(f)
                if scenario_data['name'] == name:
                    os.remove(os.path.join('scenarios', filename))
                    deleted = True
        except Exception as e:
            print(f"Error deleting scenario {filename}: {e}")
    
    return deleted

def export_scenario(name, format='json'):
    """
    Exports a scenario to a file.
    
    Args:
        name: Name of the scenario to export
        format: Format to export (json, csv)
    
    Returns:
        Path to exported file or None if failed
    """
    ensure_scenarios_dir()
    
    # Load the latest version of the scenario
    scenarios = load_scenario()
    if name not in scenarios:
        return None
    
    data = scenarios[name]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    if format.lower() == 'json':
        # Export as JSON
        export_filename = f"export_{name.replace(' ', '_')}_{timestamp}.json"
        export_path = os.path.join('scenarios', export_filename)
        
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return export_path
    
    elif format.lower() == 'csv':
        # Export as CSV (simplified)
        export_filename = f"export_{name.replace(' ', '_')}_{timestamp}.csv"
        export_path = os.path.join('scenarios', export_filename)
        
        # Convert the scenario data to a flat structure for CSV
        flat_data = {}
        flat_data['institution_name'] = data.get('institution_name', '')
        flat_data['total_students'] = data.get('total_students', 0)
        flat_data['total_teachers'] = data.get('total_teachers', 0)
        flat_data['num_classrooms'] = data.get('num_classrooms', 0)
        flat_data['ideal_ratio'] = data.get('ideal_ratio', 0)
        
        # Add subject-specific data
        for i, subject in enumerate(data.get('subject_names', [])):
            flat_data[f'subject_{i+1}_name'] = subject
            flat_data[f'subject_{i+1}_difficulty'] = data.get('subject_difficulties', {}).get(subject, 0)
            flat_data[f'subject_{i+1}_teacher_percentage'] = data.get('teacher_distribution', {}).get(subject, 0)
        
        # Create DataFrame and export
        df = pd.DataFrame([flat_data])
        df.to_csv(export_path, index=False)
        
        return export_path
    
    else:
        # Unsupported format
        return None

def import_scenario(file_path):
    """
    Imports a scenario from a file.
    
    Args:
        file_path: Path to the file to import
    
    Returns:
        True if successful, False otherwise
    """
    try:
        filename = os.path.basename(file_path)
        
        if filename.endswith('.json'):
            # Import JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract scenario name from filename
            name_parts = filename.split('_')
            if filename.startswith('export_'):
                name = name_parts[1]
            else:
                name = name_parts[0]
            
            # Replace underscores with spaces
            name = name.replace('_', ' ')
            
            # Save as a new scenario
            save_scenario(name, data)
            return True
        
        elif filename.endswith('.csv'):
            # Import CSV
            df = pd.read_csv(file_path)
            
            # Extract data from DataFrame
            data = {}
            data['institution_name'] = df.get('institution_name', [''])[0]
            data['total_students'] = int(df.get('total_students', [0])[0])
            data['total_teachers'] = int(df.get('total_teachers', [0])[0])
            data['num_classrooms'] = int(df.get('num_classrooms', [0])[0])
            data['ideal_ratio'] = float(df.get('ideal_ratio', [0])[0])
            
            # Extract subject data
            subject_columns = [col for col in df.columns if col.startswith('subject_')]
            subject_names = []
            subject_difficulties = {}
            teacher_distribution = {}
            
            for i in range(1, 100):  # Arbitrary upper limit
                name_col = f'subject_{i}_name'
                diff_col = f'subject_{i}_difficulty'
                dist_col = f'subject_{i}_teacher_percentage'
                
                if name_col not in df.columns:
                    break
                
                subject_name = df[name_col][0]
                subject_names.append(subject_name)
                
                if diff_col in df.columns:
                    subject_difficulties[subject_name] = float(df[diff_col][0])
                
                if dist_col in df.columns:
                    teacher_distribution[subject_name] = float(df[dist_col][0])
            
            data['subject_names'] = subject_names
            data['subject_difficulties'] = subject_difficulties
            data['teacher_distribution'] = teacher_distribution
            
            # Extract scenario name from filename
            name_parts = filename.split('_')
            if filename.startswith('export_'):
                name = name_parts[1]
            else:
                name = name_parts[0]
            
            # Replace underscores with spaces
            name = name.replace('_', ' ')
            
            # Save as a new scenario
            save_scenario(name, data)
            return True
        
        else:
            # Unsupported format
            return False
    
    except Exception as e:
        print(f"Error importing scenario: {e}")
        return False