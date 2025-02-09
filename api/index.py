from flask import Flask, send_file
import os
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from request_spotters import get_spotters_positions, create_map

app = Flask(__name__)

# Create a directory for temporary files
TEMP_DIR = '/tmp'
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def serve_map():
    # Your spotter IDs
    APPLICATION_ID = "55f78b6ed31f5"
    marker_ids = [50305, 23412, 45939]
    
    try:
        # Get spotter data and create map
        result = get_spotters_positions(APPLICATION_ID, marker_ids)
        if result:
            map_file = create_map(result.get('positions', []), TEMP_DIR)
            return send_file(map_file)
        else:
            return "Error: No data received from spotters", 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500 