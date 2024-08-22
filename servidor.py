from flask import Flask, request, jsonify
from datetime import datetime
from meteostat import Point, Hourly
import pandas as pd
from io import StringIO

app = Flask(__name__)

def obtener_datos_meteorologicos(lat, lon, alt, start, end):
    locacion = Point(lat, lon)
    data = Hourly(locacion, start, end)
    data = data.fetch()
    
    print(f"Datos obtenidos de la API: {data}")
    
    if data.empty:
        return None, None
    
    if 'rhum' in data.columns:
        ultima_hora = data.tail(1)
        temp = ultima_hora['temp'].values[0]
        rhum = ultima_hora['rhum'].values[0]
        return temp, rhum
    else:
        column_info = f"Available columns in weather data:\n{data.columns}"
        temp_data = data[['tavg', 'tmin', 'tmax']].tail(1).to_string()
        return column_info, temp_data

@app.route('/add_marker')
def add_marker():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        print(f'Recibido lat: {lat}, lon: {lon}')  # Añade esto para depuración
        start = datetime(2024, 8, 19)
        end = datetime(2024, 8, 20)
        temp, rhum = obtener_datos_meteorologicos(lat, lon, 70, start, end)

        if temp is None and rhum is None:
            return jsonify({'error': 'Información no encontrada'}), 404

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if rhum is not None:
            return jsonify({'temp': temp, 'rhum': rhum, 'time': current_datetime})
        else:
            return jsonify({
                'station_name': 'First Station Name: Potosi',
                'column_info': temp,
                'temperature_data': rhum,
                'time': current_datetime
            })

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/')
def index():
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #Data ejemplo
    data_csv = f"""Latitude,Longitude,Temperature,Humidity,Time
    34.05,-118.25,25.0,60,{current_datetime}
    40.71,-74.01,20.0,70,{current_datetime}
    37.77,-122.42,18.0,80,{current_datetime}
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
                    radius:  8,
                    color: 'blue',
                    fill: true,
                    fillColor: 'blue'
                }}).bindPopup(
                    'Temperature: ' + marker.Temperature + ' °C<br>' +
                    'Humidity: ' + marker.Humidity + ' %<br>' +
                    'Time: ' + marker.Time
                ).addTo(map);
            }});

            function addMarker(e) {{
                var lat = e.latlng.lat;
                var lon = e.latlng.lng;
                console.log('Clicked at: ' + lat + ', ' + lon);
                var url = '/add_marker?lat=' + lat + '&lon=' + lon;
                fetch(url).then(response => response.json()).then(data => {{
                    if (data.error) {{
                        alert(data.error);
                    }} else if (data.rhum) {{
                        var popupText = 'Temperature: ' + data.temp + ' °C<br>Humidity: ' + data.rhum + ' %<br>Time: ' + data.time;
                    }} else {{
                        var popupText = 'Station: ' + data.station_name + '<br>' +
                                        'Column Info: ' + data.column_info.replace(/\\n/g, '<br>') + '<br>' +
                                        'Temperature Data: ' + data.temperature_data.replace(/\\n/g, '<br>') + '<br>' +
                                        'Time: ' + data.time;
                    }}
                    L.circleMarker([lat, lon], {{
                        radius:  5,  // Tamaño fijo para todos los círculos
                        color: 'blue',
                        fill: true,
                        fillColor: 'blue'
                    }}).bindPopup(popupText).addTo(map);
                }}).catch(error => console.error('Error:', error));
            }}

            map.on('click', addMarker);
        </script>
    </body>
    </html>
    """

    return map_html

if __name__ == '__main__':
    app.run(debug=True)
