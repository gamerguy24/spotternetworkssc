import requests
import json
import sys
import folium
from datetime import datetime
import time
import webbrowser
import os
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from pathlib import Path

def get_spotters_positions(application_id, marker_ids):
    """
    Request specific spotters' positions using their marker IDs.
    
    Args:
        application_id (str): Your application ID
        marker_ids (list): List of marker IDs to retrieve positions for
        
    Returns:
        dict: JSON response containing positions data
    """
    
    url = "https://private-anon-ed8275e084-spotternetwork.apiary-proxy.com/positions"
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Origin": "*"
    }
    
    payload = {
        "id": application_id,
        "markers": marker_ids
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        # Log response headers for debugging
        print("\nResponse Headers:")
        print("-" * 20)
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        print("-" * 20 + "\n")
        
        data = response.json()
        
        for position in data.get('positions', []):
            print("-" * 50)
            print(f"Spotter Information:")
            print(f"Name: {position.get('first', 'N/A')} {position.get('last', 'N/A')}")
            print(f"Location: {position.get('lat', 'N/A')}, {position.get('lon', 'N/A')}")
            print(f"Elevation: {position.get('elev', 'N/A')} m")
            print(f"Direction: {position.get('dir', 'N/A')}°")
            print(f"GPS Status: {position.get('gps', 'N/A')}")
            print(f"Reported: {position.get('report_at', 'N/A')} (Unix: {position.get('unix', 'N/A')})")
            
            # Contact Information
            if any([position.get('callsign'), position.get('email'), position.get('phone')]):
                print("\nContact:")
                if position.get('callsign'):
                    print(f"Callsign: {position['callsign']}")
                if position.get('email'):
                    print(f"Email: {position['email']}")
                if position.get('phone'):
                    print(f"Phone: {position['phone']}")
            
            # Radio Information
            if any([position.get('ham'), position.get('ham_show'), position.get('freq')]):
                print("\nRadio:")
                if position.get('ham'):
                    print(f"HAM: {position['ham']}")
                if position.get('ham_show'):
                    print(f"HAM Show: {position['ham_show']}")
                if position.get('freq'):
                    print(f"Frequency: {position['freq']}")
            
            # Social Media & Web
            if any([position.get('im'), position.get('twitter'), position.get('web')]):
                print("\nSocial/Web:")
                if position.get('im'):
                    print(f"IM: {position['im']}")
                if position.get('twitter'):
                    print(f"Twitter: {position['twitter']}")
                if position.get('web'):
                    print(f"Website: {position['web']}")
            
            if position.get('note'):
                print(f"\nNote: {position['note']}")
            
            print(f"Marker ID: {position.get('marker', 'N/A')}")
            print("-" * 50)
            print()
            
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error parsing response: Missing field {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def start_web_server(port=8000):
    """
    Start a simple HTTP server to serve the map
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    
    # Run server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"\nMap server started at http://localhost:{port}")
    return httpd

def create_map(positions):
    """
    Create an interactive map showing spotter locations with auto-refresh.
    
    Args:
        positions (list): List of spotter position dictionaries
    """
    # Create a map centered on the first spotter, or US center if no spotters
    if positions:
        center_lat = float(positions[0].get('lat', 39.8283))
        center_lon = float(positions[0].get('lon', -98.5795))
    else:
        center_lat, center_lon = 39.8283, -98.5795  # Center of US
    
    # Create the map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add markers for each spotter
    for position in positions:
        try:
            lat = float(position.get('lat', 0))
            lon = float(position.get('lon', 0))
            
            # Create popup content
            popup_content = f"""
                <b>{position.get('first', '')} {position.get('last', '')}</b><br>
                Reported: {position.get('report_at', 'N/A')}<br>
                Elevation: {position.get('elev', 'N/A')}m<br>
                Direction: {position.get('dir', 'N/A')}°<br>
                """
            if position.get('note'):
                popup_content += f"Note: {position['note']}<br>"
            
            # Add marker to map
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{position.get('first', '')} {position.get('last', '')}"
            ).add_to(m)
            
        except (ValueError, TypeError) as e:
            print(f"Error adding marker for {position.get('first', '')} {position.get('last', '')}: {e}")
    
    # Add NOAA Weather Radar Layer
    radar_layer = folium.TileLayer(
        name='NOAA Weather Radar',
        tiles='https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/nexrad-n0q-900913/{z}/{x}/{y}.png?_=' + str(int(time.time())),
        attr='Weather data © NOAA',
        overlay=True,
        opacity=0.7
    )
    radar_layer.add_to(m)
    
    # Add layer control to toggle radar
    folium.LayerControl(position='topright').add_to(m)
    
    # Add auto-refresh meta tag and last update time with better formatting
    auto_refresh_script = f"""
    <script>
        // Add company banner
        var banner = document.createElement('div');
        banner.style.position = 'fixed';
        banner.style.top = '10px';
        banner.style.left = '50%';
        banner.style.transform = 'translateX(-50%)';
        banner.style.background = 'rgba(0, 0, 0, 0.8)';
        banner.style.color = 'white';
        banner.style.padding = '12px 24px';
        banner.style.borderRadius = '5px';
        banner.style.zIndex = '1000';
        banner.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
        banner.style.fontFamily = 'Arial, sans-serif';
        banner.style.fontSize = '20px';
        banner.style.fontWeight = 'bold';
        banner.style.letterSpacing = '1px';
        banner.style.textTransform = 'uppercase';
        banner.innerHTML = '⚡ Southern Style Storm Chasen LLC ⚡';
        document.body.appendChild(banner);

        // Add last update time with live clock and date
        var lastUpdate = document.createElement('div');
        lastUpdate.style.position = 'fixed';
        lastUpdate.style.bottom = '10px';
        lastUpdate.style.left = '10px';
        lastUpdate.style.background = 'rgba(255, 255, 255, 0.9)';
        lastUpdate.style.padding = '8px 12px';
        lastUpdate.style.borderRadius = '5px';
        lastUpdate.style.zIndex = '1000';
        lastUpdate.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
        lastUpdate.style.fontFamily = 'Arial, sans-serif';
        lastUpdate.style.fontSize = '14px';
        
        // Add LIVE indicator
        var liveIndicator = document.createElement('span');
        liveIndicator.style.color = '#ff0000';
        liveIndicator.style.marginRight = '8px';
        liveIndicator.style.animation = 'blink 2s infinite';
        
        // Add blinking animation
        var style = document.createElement('style');
        style.textContent = `
            @keyframes blink {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
        `;
        document.head.appendChild(style);
        
        function updateClock() {{
            var now = new Date();
            var date = now.toLocaleDateString('en-US', {{
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            }});
            var time = now.toLocaleTimeString('en-US', {{
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            }});
            
            liveIndicator.innerHTML = '● LIVE';
            lastUpdate.innerHTML = '';
            lastUpdate.appendChild(liveIndicator);
            lastUpdate.appendChild(document.createTextNode(date + ' ' + time));
        }}
        
        // Update clock every second
        updateClock();
        setInterval(updateClock, 1000);
        document.body.appendChild(lastUpdate);
        
        // Add radar refresh function
        function refreshRadar() {{
            var mapLayers = document.querySelectorAll('img.leaflet-tile');
            mapLayers.forEach(function(layer) {{
                if (layer.src.includes('mesonet.agron.iastate.edu')) {{
                    layer.src = layer.src.split('?')[0] + '?_=' + new Date().getTime();
                }}
            }});
        }}
        
        // Refresh radar every 30 seconds
        setInterval(refreshRadar, 30000);
    </script>
    """
    
    # Save with a fixed filename instead of timestamp-based name
    map_file = "spotters_map.html"
    m.save(map_file)
    
    # Add auto-refresh script to the file
    with open(map_file, 'r', encoding='utf-8') as file:
        content = file.read()
    with open(map_file, 'w', encoding='utf-8') as file:
        # Insert auto-refresh script before </body>
        content = content.replace('</body>', f'{auto_refresh_script}</body>')
        file.write(content)
    
    return map_file

def auto_refresh_map(application_id, marker_ids, refresh_interval=60):
    """
    Continuously update the map at specified intervals.
    
    Args:
        application_id (str): Your application ID
        marker_ids (list): List of marker IDs to monitor
        refresh_interval (int): Seconds between updates
    """
    # Start the web server
    server = start_web_server()
    map_file = "spotters_map.html"
    
    try:
        while True:
            # Get new data and update map
            result = get_spotters_positions(application_id, marker_ids)
            create_map(result.get('positions', []))
            
            # Open browser only on first run
            if not hasattr(auto_refresh_map, '_browser_opened'):
                webbrowser.open(f'http://localhost:8000/{map_file}')
                auto_refresh_map._browser_opened = True
            
            print(f"\nMap updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next update in {refresh_interval} seconds...")
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\nStopping map updates...")
        server.shutdown()
    except Exception as e:
        print(f"\nError in auto-refresh: {e}")
        server.shutdown()

def load_spotter_list():
    """Load the list of spotter IDs from spotters.json"""
    spotter_file = Path("spotters.json")
    if spotter_file.exists():
        with open(spotter_file, "r") as f:
            return json.load(f)
    return {
        "active_spotters": [50305, 23412],  # Your default spotters
        "watch_region": {
            "min_lat": 25.0,  # Southern boundary (Florida)
            "max_lat": 45.0,  # Northern boundary (roughly Michigan)
            "min_lon": -100.0,  # Western boundary (roughly Texas)
            "max_lon": -75.0   # Eastern boundary (roughly East Coast)
        }
    }

def save_spotter_list(spotter_data):
    """Save the current list of spotter IDs"""
    with open("spotters.json", "w") as f:
        json.dump(spotter_data, f, indent=2)

def main():
    """
    Main function to run the spotter position lookup.
    Creates a self-refreshing map file.
    """
    APPLICATION_ID = "55f78b6ed31f5"
    
    print("\nSpotter Network Position Lookup")
    print("-" * 30)
    
    # Use fixed marker IDs
    marker_ids = [50305, 23412, 45939]  # Added spotter ID 45939
    print(f"Using marker IDs: {marker_ids}")
    
    try:
        # Start continuous updates
        while True:
            # Get spotter data and create map
            result = get_spotters_positions(APPLICATION_ID, marker_ids)
            if result:
                create_map(result.get('positions', []))
                print(f"\nTracking {len(marker_ids)} spotters")
                print(f"Next update in 30 seconds...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nStopping updates...")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 