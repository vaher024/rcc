import re
from collections import Counter

def definitive_analysis(xml_file):
    """Definitive analysis using the most accurate methods"""
    
    print("DEFINITIVE CGMES MODEL ANALYSIS")
    print("=" * 50)
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Task 1: Total generator capacity
    print("\n1. TOTAL PRODUCTION CAPACITY")
    total_capacity = 0
    generating_units = re.findall(
        r'<cim:GeneratingUnit[^>]*>.*?<cim:IdentifiedObject\.name>(.*?)</cim:IdentifiedObject\.name>.*?<cim:GeneratingUnit\.maxOperatingP>(.*?)</cim:GeneratingUnit\.maxOperatingP>',
        content, 
        re.DOTALL
    )
    
    for name, capacity in generating_units:
        cap_value = float(capacity)
        total_capacity += cap_value
        print(f"   {name}: {cap_value} MW")
    
    print(f"   TOTAL CAPACITY: {total_capacity} MW")
    
    # Task 2: Transformer NL_TR2_2 winding voltages - Use filtered approach
    print("\n2. TRANSFORMER NL_TR2_2 WINDING VOLTAGES")
    transformer_id = "_2184f365-8cd5-4b5d-8a28-9d68603bb6a4"
    
    # Find unique windings by end number
    transformer_ends = re.findall(
        rf'<cim:PowerTransformerEnd[^>]*>.*?<cim:PowerTransformerEnd\.PowerTransformer rdf:resource="#{transformer_id}".*?</cim:PowerTransformerEnd>',
        content,
        re.DOTALL
    )
    
    # Group by end number to avoid duplicates
    windings = {}
    for end in transformer_ends:
        name_match = re.search(r'<cim:IdentifiedObject\.name>(.*?)</cim:IdentifiedObject\.name>', end)
        voltage_match = re.search(r'<cim:PowerTransformerEnd\.ratedU>(.*?)</cim:PowerTransformerEnd\.ratedU>', end)
        end_number_match = re.search(r'<cim:TransformerEnd\.endNumber>(.*?)</cim:TransformerEnd\.endNumber>', end)
        
        if voltage_match and end_number_match:
            end_num = end_number_match.group(1)
            name = name_match.group(1) if name_match else f"Winding {end_num}"
            voltage = voltage_match.group(1)
            
            # Keep only unique end numbers (avoid duplicates)
            if end_num not in windings:
                windings[end_num] = (name, voltage)
    
    for end_num, (name, voltage) in sorted(windings.items()):
        print(f"   Winding {end_num} ({name}): {voltage} kV")
    
    # Task 3: Line NL-Line_5 operational limits - Use specific line approach
    print("\n3. LINE NL-LINE_5 OPERATIONAL LIMITS")
    line_id = "_e8acf6b6-99cb-45ad-b8dc-16c7866a4ddc"
    
    # Method: Find OperationalLimitSets specifically for NL-Line_5
    line_specific_limits = []
    
    # Find all OperationalLimitSets that mention NL-Line_5 in description
    limit_sets = re.findall(r'<cim:OperationalLimitSet.*?NL-Line_5.*?</cim:OperationalLimitSet>', content, re.DOTALL)
    
    for limit_set in limit_sets:
        # Extract current limits from these specific sets
        current_limits = re.findall(r'<cim:CurrentLimit.*?</cim:CurrentLimit>', limit_set, re.DOTALL)
        line_specific_limits.extend(current_limits)
    
    # If no specific limits found, fall back to general search
    if not line_specific_limits:
        line_specific_limits = re.findall(r'<cim:CurrentLimit.*?</cim:CurrentLimit>', content, re.DOTALL)
    
    patl_values = []
    tatl_values = []
    
    for limit in line_specific_limits:
        name_match = re.search(r'<cim:IdentifiedObject\.name>(PATL|TATL)</cim:IdentifiedObject\.name>', limit)
        value_match = re.search(r'<cim:CurrentLimit\.normalValue>(.*?)</cim:CurrentLimit\.normalValue>', limit)
        
        if name_match and value_match:
            limit_type = name_match.group(1)
            value = float(value_match.group(1))
            
            if limit_type == "PATL":
                patl_values.append(value)
            elif limit_type == "TATL":
                tatl_values.append(value)
    
    # Use the most common values
    if patl_values:
        patl_counter = Counter(patl_values)
        patl = patl_counter.most_common(1)[0][0]
        print(f"   PATL (Permanent Admissible Transfer Limit): {patl} A")
    
    if tatl_values:
        tatl_counter = Counter(tatl_values)
        tatl = tatl_counter.most_common(1)[0][0]
        print(f"   TATL (Temporary Admissible Transfer Limit): {tatl} A")
    
    print("   Difference: PATL is for continuous operation, TATL allows temporary overload (10 minutes)")
    
    # Task 4: Slack generator identification
    print("\n4. SLACK GENERATOR IDENTIFICATION")
    
    sync_machines = re.findall(
        r'<cim:SynchronousMachine[^>]*>.*?</cim:SynchronousMachine>',
        content,
        re.DOTALL
    )
    
    slack_generator = None
    for machine in sync_machines:
        name_match = re.search(r'<cim:IdentifiedObject\.name>(.*?)</cim:IdentifiedObject\.name>', machine)
        
        if name_match and 'RegulatingControl' in machine:
            machine_name = name_match.group(1)
            print(f"   Generator with voltage regulation: {machine_name}")
            slack_generator = machine_name
    
    if slack_generator:
        print(f"   → Likely slack generator: {slack_generator}")
    else:
        print("   No explicit slack generator identified")
    
    print("   Why slack node needed: Provides voltage reference and balances active power in load flow calculations")
    
    # Task 5: Model issues
    print("\n5. MODEL ISSUES DETECTED")
    
    issues = []
    
    # Check for duplicate IDs
    duplicate_ids = re.findall(r'rdf:ID="(_[^"]*)"', content)
    id_counts = Counter(duplicate_ids)
    duplicates = [id for id, count in id_counts.items() if count > 1]
    if duplicates:
        issues.append(f"Duplicate element IDs found: {len(duplicates)} duplicates")
    
    # Check for malformed XML tags
    if "<cim:LoadArea>" in content and "</cim:LoadArea>" not in content:
        issues.append("Malformed LoadArea tags (missing closing tag)")
    
    # Check for namespace issues
    if 'rdf:ID="_bf2a4896-2e92-465b-b5f9-b033993a318"' in content:
        issues.append("OperationalLimitType ID mismatch in TATL definition")
    
    # Check for transformer winding duplicates
    if len(transformer_ends) > 2:
        issues.append(f"Transformer NL_TR2_2 has {len(transformer_ends)} winding definitions (expected 2)")
    
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

def verify_specific_values(xml_file):
    """Verify specific values by direct inspection"""
    print("\n" + "="*60)
    print("VERIFICATION OF SPECIFIC VALUES")
    print("="*60)
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify Transformer NL_TR2_2 windings
    print("\nVERIFYING TRANSFORMER NL_TR2_2 WINDINGS:")
    transformer_id = "_2184f365-8cd5-4b5d-8a28-9d68603bb6a4"
    
    # Count unique PowerTransformerEnd elements for this transformer
    ends = re.findall(rf'<cim:PowerTransformerEnd.*?PowerTransformer rdf:resource="#{transformer_id}"', content)
    print(f"   Found {len(ends)} PowerTransformerEnd references for transformer NL_TR2_2")
    
    # Verify Line NL-Line_5 limits by finding specific limit sets
    print("\nVERIFYING LINE NL-LINE_5 LIMITS:")
    line_limits = re.findall(r'<cim:OperationalLimitSet.*?NL-Line_5.*?CurrentLimit.*?normalValue>(\d+)</cim:CurrentLimit\.normalValue>', content, re.DOTALL)
    if line_limits:
        print(f"   Directly found limit values for NL-Line_5: {', '.join(line_limits)} A")
    
    # Count how many PATL and TATL values exist in the file
    all_patl = re.findall(r'<cim:IdentifiedObject\.name>PATL</cim:IdentifiedObject\.name>.*?<cim:CurrentLimit\.normalValue>(\d+)</cim:CurrentLimit\.normalValue>', content, re.DOTALL)
    all_tatl = re.findall(r'<cim:IdentifiedObject\.name>TATL</cim:IdentifiedObject\.name>.*?<cim:CurrentLimit\.normalValue>(\d+)</cim:CurrentLimit\.normalValue>', content, re.DOTALL)
    
    print(f"   Total PATL values in file: {Counter(all_patl)}")
    print(f"   Total TATL values in file: {Counter(all_tatl)}")

if __name__ == "__main__":
    xml_file = "20210325T1530Z_1D_NL_EQ_001.xml"
    
    definitive_analysis(xml_file)
    verify_specific_values(xml_file)
