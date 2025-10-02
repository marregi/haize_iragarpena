import pandas as pd
from datetime import datetime, timedelta
import json
import random

# --- ID de tu Google Sheet ---
GSHEET_ID = "1rcxEcpwdHDFD5bRM8gu_5xU3ZDz8nEtj"

# --- Función para cargar todas las hojas públicas ---
def load_all_sheets(gsheet_id: str) -> dict[str, pd.DataFrame]:
    sheet_tabs = {
        "Badia": "129655069",
        "Elgea": "408081399",
        "Corrella": "107505326"
    }
    dfs = {}
    for name, gid in sheet_tabs.items():
        url = f"https://docs.google.com/spreadsheets/d/{gsheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        dfs[name] = df
    return dfs

# --- Filtrar datos de hace un año ---
def get_data_one_year_ago(df, fecha_col="timestamp"):
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    df = df.copy()
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    mask = (
        (df[fecha_col].dt.year == one_year_ago.year) &
        (df[fecha_col].dt.month == one_year_ago.month) &
        (df[fecha_col].dt.day == one_year_ago.day) &
        (df[fecha_col].dt.hour == one_year_ago.hour)
    )
    return df[mask], one_year_ago

# --- Generar pronóstico por estación ---
def generate_station_forecast(df, station_name):
    """Genera pronóstico específico para una estación"""
    if {"timestamp", "wind_mps"}.issubset(df.columns):
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["wind_mps"] = pd.to_numeric(df["wind_mps"].astype(str).str.replace(',', '.'), errors="coerce")
        df = df.dropna(subset=['timestamp', 'wind_mps'])
        
        if df.empty:
            return None
            
        # Obtener últimos 30 días para calcular tendencias
        df = df.sort_values("timestamp")
        ult_fecha = df["timestamp"].max()
        df_recent = df[df["timestamp"] > (ult_fecha - pd.Timedelta(days=30))]
        
        if df_recent.empty:
            return None
        
        # Calcular promedios por hora del día para patrones diarios
        df_recent = df_recent.copy()  # Evitar advertencias de pandas
        df_recent['hour'] = df_recent['timestamp'].dt.hour
        hourly_avg = df_recent.groupby('hour')['wind_mps'].mean()
        
        # Calcular promedio general
        general_avg = df_recent['wind_mps'].mean()
        
        # Generar pronóstico para los próximos 3 días con detalle horario
        forecast_data = []
        start_date = ult_fecha + pd.Timedelta(days=1)
        
        for day_offset in range(3):
            current_date = start_date + pd.Timedelta(days=day_offset)
            day_forecasts = []
            
            # Generar pronóstico para horas específicas del día (cada 3 horas)
            for hour in [6, 9, 12, 15, 18, 21]:
                # Usar patrón horario si existe, sino usar promedio general
                if hour in hourly_avg:
                    base_value = hourly_avg[hour]
                else:
                    base_value = general_avg
                
                # Añadir pequeña variación aleatoria basada en variabilidad histórica
                std_dev = df_recent['wind_mps'].std()
                import random
                variation = random.uniform(-0.2 * std_dev, 0.2 * std_dev)
                forecast_value = max(0, base_value + variation)
                
                day_forecasts.append({
                    'datetime': current_date.replace(hour=hour),
                    'hour': f"{hour:02d}:00",
                    'wind_mps': round(forecast_value, 1)
                })
            
            forecast_data.append({
                'date': current_date.strftime('%d/%m/%Y'),
                'date_short': current_date.strftime('%d/%m'),
                'weekday': current_date.strftime('%A'),
                'hours': day_forecasts
            })
        
        return forecast_data
    
    return None

# --- Generar HTML ---
def generate_html(parques_data, forecast_by_station, timestamp):
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pronóstico de Viento - Parques Eólicos</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}
        
        .update-time {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .parks-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .park-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .park-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .park-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .park-icon {{
            font-size: 2em;
        }}
        
        .park-name {{
            font-size: 1.5em;
            font-weight: 600;
            color: #333;
        }}
        
        .data-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .data-row:last-child {{
            border-bottom: none;
        }}
        
        .data-label {{
            color: #666;
            font-weight: 500;
        }}
        
        .data-value {{
            color: #333;
            font-weight: 600;
        }}
        
        .no-data {{
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }}
        
        .forecast-section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }}
        
        .forecast-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 3px solid #764ba2;
        }}
        
        .forecast-title {{
            font-size: 1.8em;
            font-weight: 600;
            color: #333;
        }}
        
        .forecast-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .forecast-day {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            transition: transform 0.3s ease;
        }}
        
        .forecast-day:hover {{
            transform: scale(1.02);
        }}
        
        .forecast-date {{
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }}
        
        .forecast-hours {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }}
        
        .forecast-hour {{
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        
        .forecast-time {{
            font-size: 0.8em;
            margin-bottom: 5px;
            opacity: 0.9;
        }}
        
        .forecast-value {{
            font-size: 1.2em;
            font-weight: 700;
        }}
        
        .forecast-unit {{
            font-size: 0.7em;
            opacity: 0.8;
        }}
        
        .station-forecast {{
            margin-top: 25px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
        }}
        
        .station-forecast-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .station-forecast-title {{
            font-size: 1.2em;
            font-weight: 600;
            color: #667eea;
        }}
        
        .historical-note {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #ffc107;
        }}
        
        .historical-note strong {{
            color: #856404;
        }}
        
        @media (max-width: 768px) {{
            .parks-grid {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
            
            .forecast-grid {{
                grid-template-columns: 1fr;
            }}
            
            .forecast-hours {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <span>🌬️</span>
                Pronóstico de Viento - Parques Eólicos
            </h1>
            <div class="update-time">
                Última actualización: {timestamp}
            </div>
        </header>
        
        <div class="historical-note">
            <strong>📊 Datos Históricos:</strong> Comparativa con el mismo día y hora hace un año
        </div>
        
        <br>
        
        <div class="parks-grid">
"""
    
    # Agregar datos de cada parque
    for park_name, park_info in parques_data.items():
        html += f"""
            <div class="park-card">
                <div class="park-header">
                    <span class="park-icon">⚡</span>
                    <span class="park-name">{park_name}</span>
                </div>
"""
        
        if park_info['has_data']:
            html += f"""
                <div class="data-row">
                    <span class="data-label">Fecha de referencia:</span>
                    <span class="data-value">{park_info['fecha_ref']}</span>
                </div>
"""
            # Agregar todas las columnas disponibles
            for col, value in park_info['data'].items():
                if col != 'timestamp' and col != 'fechas':
                    html += f"""
                <div class="data-row">
                    <span class="data-label">{col}:</span>
                    <span class="data-value">{value}</span>
                </div>
"""
        else:
            html += """
                <div class="no-data">
                    No hay datos disponibles para esta fecha
                </div>
"""
        
        # Agregar pronóstico específico de la estación
        if park_name in forecast_by_station and forecast_by_station[park_name]:
            html += """
                <div class="station-forecast">
                    <div class="station-forecast-header">
                        <span>📈</span>
                        <span class="station-forecast-title">Pronóstico 3 días</span>
                    </div>
"""
            
            for day_data in forecast_by_station[park_name]:
                html += f"""
                    <div class="forecast-day" style="margin-bottom: 15px;">
                        <div class="forecast-date">{day_data['date']} - {day_data['weekday']}</div>
                        <div class="forecast-hours">
"""
                
                for hour_data in day_data['hours']:
                    html += f"""
                            <div class="forecast-hour">
                                <div class="forecast-time">{hour_data['hour']}</div>
                                <div class="forecast-value">{hour_data['wind_mps']}</div>
                                <div class="forecast-unit">m/s</div>
                            </div>
"""
                
                html += """
                        </div>
                    </div>
"""
            
            html += """
                </div>
"""
        
        html += """
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    return html

# --- Main execution ---
def main():
    # Timestamp de ejecución
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Cargar datos
    parques = load_all_sheets(GSHEET_ID)
    
    # Procesar datos de cada parque
    parques_data = {}
    for nombre, df in parques.items():
        df_sel, fecha_ref = get_data_one_year_ago(df, fecha_col="timestamp")
        
        if not df_sel.empty:
            # Convertir la primera fila a diccionario
            data_dict = df_sel.iloc[0].to_dict()
            parques_data[nombre] = {
                'has_data': True,
                'fecha_ref': fecha_ref.strftime('%Y-%m-%d %H:00'),
                'data': data_dict
            }
        else:
            parques_data[nombre] = {
                'has_data': False,
                'fecha_ref': None,
                'data': {}
            }
    
    # Generar pronósticos por estación
    forecast_by_station = {}
    for nombre, df in parques.items():
        forecast = generate_station_forecast(df, nombre)
        forecast_by_station[nombre] = forecast
    
    # Generar HTML
    html_content = generate_html(parques_data, forecast_by_station, timestamp)
    
    # Guardar archivo
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML generado exitosamente: index.html")
    print(f"📅 Timestamp: {timestamp}")
    print(f"📊 Pronósticos generados para {len(forecast_by_station)} estaciones")

if __name__ == "__main__":
    main()
