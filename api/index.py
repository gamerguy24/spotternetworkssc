from flask import Flask, send_file, Response
import os
import sys
import tempfile

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from request_spotters import get_spotters_positions, create_map

app = Flask(__name__)

@app.route('/')
def serve_map():
    # Your spotter IDs
    APPLICATION_ID = "55f78b6ed31f5"
    marker_ids = [50305, 23412, 45939]
    
    try:
        # Get spotter data and create map
        result = get_spotters_positions(APPLICATION_ID, marker_ids)
        if result:
            # Create a temporary file using tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w+') as tmp:
                map_file = create_map(result.get('positions', []), os.path.dirname(tmp.name))
                
                # Read the file content
                with open(map_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Clean up the temporary files
                try:
                    os.unlink(map_file)
                except:
                    pass
                
                # Return the content directly
                return Response(content, mimetype='text/html')
        else:
            return "Error: No data received from spotters", 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500 