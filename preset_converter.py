import xml.etree.ElementTree as ET
import json
import os

def xml_to_sine_preset(xml_path):
    """
    Convert an XML preset file to a SINE preset format
    
    Args:
        xml_path (str): Path to the XML preset file
        
    Returns:
        dict: A dictionary in the SINE preset format
    """
    try:
        # Parse XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get preset title/name
        title = "Imported Preset"
        title_elem = root.find(".//Title")
        if title_elem is not None and title_elem.text:
            title = title_elem.text
        
        # Initialize preset data
        preset_data = {
            "name": title,
            "entrainment_points": [],
            "volume_points": [],
            "base_freq_points": []
        }
        
        # Find entrainment track (support current exporter structure)
        entrainment_track = root.find(".//EntrainmentTrack")
        if entrainment_track is None:
            # If no entrainment track, return empty preset
            return preset_data
        
        # Get track volume
        track_volume = 0.5  # Default
        if "trackVolume" in entrainment_track.attrib:
            try:
                track_volume = float(entrainment_track.attrib["trackVolume"])
            except ValueError:
                pass
        
        # Process entrainment frequency envelope
        entrainment_freq_env = entrainment_track.find("./Envelope[@name='entrainmentFrequency']")
        if entrainment_freq_env is not None:
            for point in entrainment_freq_env.findall("./Point"):
                time = float(point.attrib.get("time", 0))
                value = float(point.attrib.get("value", 0))
                preset_data["entrainment_points"].append({"time": time, "value": value})
        
        # Process volume envelope
        volume_env = entrainment_track.find("./Envelope[@name='volume']")
        if volume_env is not None:
            for point in volume_env.findall("./Point"):
                time = float(point.attrib.get("time", 0))
                value = float(point.attrib.get("value", 0)) * track_volume  # Apply track volume
                preset_data["volume_points"].append({"time": time, "value": value})
        
        # Process base frequency envelope
        base_freq_env = entrainment_track.find("./Envelope[@name='baseFrequency']")
        if base_freq_env is not None:
            for point in base_freq_env.findall("./Point"):
                time = float(point.attrib.get("time", 0))
                value = float(point.attrib.get("value", 0))
                preset_data["base_freq_points"].append({"time": time, "value": value})
        
        # Ensure at least one point for each curve
        if not preset_data["entrainment_points"]:
            preset_data["entrainment_points"].append({"time": 0, "value": 10.0})
        if not preset_data["volume_points"]:
            preset_data["volume_points"].append({"time": 0, "value": 0.5})
        if not preset_data["base_freq_points"]:
            preset_data["base_freq_points"].append({"time": 0, "value": 100.0})
        
        return preset_data
    
    except Exception as e:
        print(f"Error converting XML preset: {e}")
        # Return a default preset in case of error
        return {
            "name": "Error - Imported Preset",
            "entrainment_points": [{"time": 0, "value": 10.0}],
            "volume_points": [{"time": 0, "value": 0.5}],
            "base_freq_points": [{"time": 0, "value": 100.0}]
        }

def sine_preset_to_xml(preset_data, output_path):
    """
    Convert a SINE preset to XML format
    
    Args:
        preset_data (dict): SINE preset data
        output_path (str): Path to save the XML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create root element
        root = ET.Element("Preset")
        
        # Get max duration from all curves
        max_time = 0
        for point_list in [preset_data["entrainment_points"], 
                         preset_data["volume_points"], 
                         preset_data["base_freq_points"]]:
            if point_list:
                max_time = max(max_time, max(p["time"] for p in point_list))
        
        root.set("length", str(max_time))
        
        # Add preset info
        info = ET.SubElement(root, "PresetInfos")
        title = ET.SubElement(info, "Title")
        title.text = preset_data.get("name", "SINE Export")
        author = ET.SubElement(info, "Author")
        author.text = "IsoFlicker Pro"
        desc = ET.SubElement(info, "Description")
        desc.text = "Created with IsoFlicker Pro SINE Editor"
        
        # Add noise envelope (empty)
        noise_env = ET.SubElement(root, "Envelope")
        noise_env.set("length", str(max_time))
        noise_env.set("name", "noise")
        noise_point = ET.SubElement(noise_env, "Point")
        noise_point.set("time", "0.0")
        noise_point.set("value", "0.0")
        
        # Add entrainment track
        track = ET.SubElement(root, "EntrainmentTrack")
        track.set("length", str(max_time))
        track.set("trackVolume", "1.0")  # We'll adjust volumes in the volume envelope
        
        # Add entrainment frequency envelope
        freq_env = ET.SubElement(track, "Envelope")
        freq_env.set("length", str(max_time))
        freq_env.set("name", "entrainmentFrequency")
        for point in preset_data.get("entrainment_points", []):
            p = ET.SubElement(freq_env, "Point")
            p.set("time", str(point["time"]))
            p.set("value", str(point["value"]))
        
        # Add volume envelope
        vol_env = ET.SubElement(track, "Envelope")
        vol_env.set("length", str(max_time))
        vol_env.set("name", "volume")
        for point in preset_data.get("volume_points", []):
            p = ET.SubElement(vol_env, "Point")
            p.set("time", str(point["time"]))
            p.set("value", str(point["value"]))
        
        # Add base frequency envelope
        base_env = ET.SubElement(track, "Envelope")
        base_env.set("length", str(max_time))
        base_env.set("name", "baseFrequency")
        for point in preset_data.get("base_freq_points", []):
            p = ET.SubElement(base_env, "Point")
            p.set("time", str(point["time"]))
            p.set("value", str(point["value"]))
        
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        return True
    
    except Exception as e:
        print(f"Error creating XML preset: {e}")
        return False

def convert_xml_to_sin(input_path, output_path=None):
    """
    Convert an XML preset file to a SINE .sin file
    
    Args:
        input_path (str): Path to the XML preset file
        output_path (str, optional): Path to save the .sin file. If None, 
                                    uses the same name with .sin extension
                                    
    Returns:
        str: Path to the output file if successful, None otherwise
    """
    try:
        # Convert to SINE preset format
        preset_data = xml_to_sine_preset(input_path)
        
        # Determine output path
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}.sin"
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
            
        return output_path
    
    except Exception as e:
        print(f"Error converting XML to SIN: {e}")
        return None

def convert_sin_to_xml(input_path, output_path=None):
    """
    Convert a SINE .sin file to an XML preset file
    
    Args:
        input_path (str): Path to the .sin file
        output_path (str, optional): Path to save the XML file. If None,
                                    uses the same name with .xml extension
                                    
    Returns:
        str: Path to the output file if successful, None otherwise
    """
    try:
        # Load SINE preset
        with open(input_path, 'r') as f:
            preset_data = json.load(f)
        
        # Determine output path
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}.xml"
        
        # Convert to XML and save
        success = sine_preset_to_xml(preset_data, output_path)
        
        if success:
            return output_path
        else:
            return None
    
    except Exception as e:
        print(f"Error converting SIN to XML: {e}")
        return None

def validate_preset_file(file_path):
    """Validate preset file format and return (is_valid, format_type).

    format_type is one of: 'sin', 'xml', or None when unsupported.
    This function is used by IntegratedIsoFlicker and must return a tuple.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.sin':
        return _validate_sin(file_path), 'sin'
    if ext == '.xml':
        return _validate_xml(file_path), 'xml'
    return False, None


def _validate_sin(file_path):
    """Validate .sin file format used by this app.

    Expected keys: entrainment_points, volume_points, base_freq_points (lists).
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        required_fields = ['entrainment_points', 'volume_points', 'base_freq_points']
        return all(isinstance(data.get(k), list) for k in required_fields)
    except Exception:
        return False


def _validate_xml(file_path):
    """Validate XML preset format.

    Accepts either our exporter format (root 'Preset' with EntrainmentTrack
    and Envelope[@name='entrainmentFrequency']) or an older simple format
    (root 'isochronic_preset' with 'frequency', 'carrier', 'volume' children).
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Newer exporter format
        if root.tag == 'Preset':
            track = root.find('.//EntrainmentTrack')
            if track is None:
                return False
            freq_env = track.find("./Envelope[@name='entrainmentFrequency']")
            return freq_env is not None

        # Older simple format
        if root.tag == 'isochronic_preset':
            for elem in ('frequency', 'carrier', 'volume'):
                if root.find(elem) is None:
                    return False
            return True

        return False
    except Exception:
        return False
