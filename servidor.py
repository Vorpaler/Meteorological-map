from flask import Flask, request, jsonify
from datetime import datetime
from meteostat import Point, Hourly, Stations
import pandas as pd
from io import StringIO

app = Flask(__name__)

def obtener_datos_meteorologicos(lat, lon, alt, start, end):
    locacion = Point(lat, lon)
    data = Hourly(locacion, start, end)
    data = data.fetch()

    # Create a Stations object
    stations = Stations()

    # Get nearby stations
    nearby_stations = stations.nearby(lat, lon)

    # Fetch the first station from the result
    first_station = nearby_stations.fetch(1)

    # Check if there's any station available
    if not first_station.empty:
        # Get the first station's details
        first_station_id = first_station.index[0]
        first_station_name = first_station.loc[first_station_id, 'name']
    else:
        first_station_name = "Nombre de la estación no disponible"

    if data.empty:
        return None, None, None, first_station_name
    
    if 'rhum' in data.columns:
        ultima_hora = data.tail(1)
        temp = ultima_hora['temp'].values[0]
        rhum = ultima_hora['rhum'].values[0]
        prcp = ultima_hora['prcp'].values[0] if 'prcp' in data.columns else 'N/A'
        return temp, rhum, prcp, first_station_name
    else:
        column_info = f"Available columns in weather data:\n{data.columns}"
        temp_data = data[['tavg', 'tmin', 'tmax']].tail(1).to_string()
        return column_info, temp_data, 'N/A', first_station_name

@app.route('/add_marker')
def add_marker():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        start = datetime(2024, 8, 19)
        end = datetime(2024, 8, 20)
        temp, rhum, prcp, station_name = obtener_datos_meteorologicos(lat, lon, 70, start, end)

        if temp is None and rhum is None and prcp is None:
            return jsonify({'error': 'Información no encontrada'}), 404

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'temp': temp, 'rhum': rhum, 'prcp': prcp, 'station_name': station_name, 'time': current_datetime})

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def index():
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Data ejemplo
    data_csv = f"""Latitude,Longitude,Temperature,Humidity,Precipitation,Time
    34.05,-118.25,25.0,60,0.0,{current_datetime}
    40.71,-74.01,20.0,70,0.1,{current_datetime}
    37.77,-122.42,18.0,80,0.0,{current_datetime}
    """

    data = pd.read_csv(StringIO(data_csv))

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        <style>
            html, body {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
            }}
            #map {{
                position: absolute;
                top: 0;
                bottom: 0;
                right: 0;
                left: 0;
            }}
        </style>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css"/>
        <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js"></script>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([37.51, -104.89333333333333], 5);

            L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);

            var markers = {data.to_dict(orient='records')};

            markers.forEach(function(marker) {{
                L.circleMarker([marker.Latitude, marker.Longitude], {{
                    radius: 8,
                    color: 'blue',
                    fill: true,
                    fillColor: 'blue'
                }}).bindPopup(
                    'Station: ' + (marker.Station || 'N/A') + '<br>' +
                    'Temperature: ' + marker.Temperature + ' °C<br>' +
                    'Humidity: ' + marker.Humidity + ' %<br>' +
                    'Precipitation: ' + marker.Precipitation + ' mm<br>' +
                    'Time: ' + marker.Time
                ).addTo(map);
            }});

            function addMarker(e) {{
                var lat = e.latlng.lat;
                var lon = e.latlng.lng;
                console.log('Clicked at: ' + lat + ', ' + lon);
                var url = '/add_marker?lat=' + lat + '&lon=' + lon;
                fetch(url)
                    .then(response => response.json())
                    .then(data => {{
                        console.log('Data received:', data);
                        var popupText;
                        if (data.temp !== undefined && data.rhum !== undefined) {{
                            popupText = 'Station: ' + (data.station_name ) + '<br>' +
                                        'Temperature: ' + data.temp + ' °C<br>' +
                                        'Humidity: ' + data.rhum + ' %<br>' +
                                        'Precipitation: ' + data.prcp + ' mm<br>' +
                                        'Time: ' + data.time;
                        }} else {{
                            popupText = 'No hay datos disponibles<br>' +
                                        'Station: ' + (data.station_name || 'N/A') + '<br>' +
                                        'Column Info: ' + (data.column_info || 'N/A').replace(/\\n/g, '<br>') + '<br>' +
                                        'Temperature Data: ' + (data.temperature_data || 'N/A').replace(/\\n/g, '<br>') + '<br>' +
                                        'Time: ' + data.time;
                        }}
                        L.circleMarker([lat, lon], {{
                            radius: 5,
                            color: 'blue',
                            fill: true,
                            fillColor: 'blue'
                        }}).bindPopup(popupText).addTo(map);
                    }})
                    .catch(error => console.error('Error:', error));
            }}

            map.on('click', addMarker);
        </script>
    </body>
    </html>
    """

    return map_html

if __name__ == '__main__':
    app.run(debug=True)
