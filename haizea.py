import pandas as pd
from datetime import datetime, timedelta
import json
import pytz

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

# --- Obtener datos del momento actual ---
def get_current_data(df, fecha_col="timestamp"):
    madrid_tz = pytz.timezone('Europe/Madrid')
    now = datetime.now(madrid_tz)
    df = df.copy()
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    # Localizar timestamps a timezone de Madrid
    df[fecha_col] = df[fecha_col].dt.tz_localize('UTC').dt.tz_convert(madrid_tz)
    
    # Buscar el dato más cercano al momento actual
    df['time_diff'] = abs((df[fecha_col] - now).dt.total_seconds())
    closest_idx = df['time_diff'].idxmin()
    
    if pd.isna(closest_idx):
        return pd.DataFrame(), now
    
    closest_data = df.loc[[closest_idx]]
    actual_time = closest_data[fecha_col].iloc[0]
    
    return closest_data, actual_time

# --- Traducir días de la semana al euskera ---
def translate_weekday_to_basque(weekday_en):
    """Traduce el nombre del día de la semana del inglés al euskera"""
    translation = {
        'Monday': 'Astelehena',
        'Tuesday': 'Asteartea',
        'Wednesday': 'Asteazkena',
        'Thursday': 'Osteguna',
        'Friday': 'Ostirala',
        'Saturday': 'Larunbata',
        'Sunday': 'Igandea'
    }
    return translation.get(weekday_en, weekday_en)

# --- Obtener pronóstico real de los próximos 5 días del sheet ---
def get_forecast_from_sheet(df, fecha_col="timestamp"):
    """Obtiene los datos de pronóstico de los próximos 5 días del sheet"""
    if {"timestamp", "wind_mps"}.issubset(df.columns):
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["wind_mps"] = pd.to_numeric(df["wind_mps"].astype(str).str.replace(',', '.'), errors="coerce")
        df = df.dropna(subset=['timestamp', 'wind_mps'])
        
        if df.empty:
            return None
            
        madrid_tz = pytz.timezone('Europe/Madrid')
        now = datetime.now(madrid_tz)
        # Localizar timestamps a timezone de Madrid
        df["timestamp"] = df["timestamp"].dt.tz_localize('UTC').dt.tz_convert(madrid_tz)
        df = df.sort_values("timestamp")
        
        # Filtrar datos futuros (desde ahora hasta 5 días adelante)
        end_date = now + timedelta(days=5)
        future_data = df[(df["timestamp"] > now) & (df["timestamp"] <= end_date)]
        
        if future_data.empty:
            return None
        
        # Agrupar por día
        forecast_data = []
        future_data = future_data.copy()  # Evitar advertencia de pandas
        future_data['date'] = future_data['timestamp'].dt.date
        
        for date, day_group in future_data.groupby('date'):
            day_forecasts = []
            
            # Ordenar por hora - TOMAR TODAS LAS HORAS DISPONIBLES (24h)
            day_group = day_group.sort_values('timestamp')
            
            # Tomar TODAS las líneas del día (las 24 horas)
            for _, row in day_group.iterrows():
                day_forecasts.append({
                    'datetime': row['timestamp'],
                    'hour': row['timestamp'].strftime('%H:%M'),
                    'wind_mps': round(row['wind_mps'], 1)
                })
            
            if day_forecasts:  # Solo agregar si hay datos
                weekday_en = pd.Timestamp(date).strftime('%A')
                forecast_data.append({
                    'date': pd.Timestamp(date).strftime('%d/%m/%Y'),
                    'date_short': pd.Timestamp(date).strftime('%d/%m'),
                    'weekday': translate_weekday_to_basque(weekday_en),
                    'hours': day_forecasts
                })
        
        return forecast_data
    
    return None

# --- Generar HTML simple para pestañas ---
def generate_html(parques_data, forecast_by_station, timestamp):
    # CSS y JavaScript básico
    head_content = '''<!DOCTYPE html>
<html lang="eu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Haize Iragarpena - Parke Eolikoak</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; padding: 20px; color: #333; }
        .container { max-width: 1800px; margin: 0 auto; }
        header { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); 
                margin-bottom: 30px; text-align: center; }
        h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .tabs-container { background: white; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); overflow: hidden; }
        .tabs-header { display: flex; background: #f8f9fa; border-bottom: 2px solid #dee2e6; }
        .tab-button { flex: 1; padding: 20px; background: none; border: none; cursor: pointer; 
                     font-size: 1.2em; font-weight: 600; color: #666; transition: all 0.3s ease; }
        .tab-button:hover { background: rgba(102, 126, 234, 0.1); color: #667eea; }
        .tab-button.active { background: #667eea; color: white; }
        .tab-content { display: none; padding: 30px; }
        .tab-content.active { display: block; }
        .current-data { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                       padding: 20px; border-radius: 12px; margin-bottom: 30px; }
        .data-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .data-item { background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; }
        .data-label { font-size: 0.8em; opacity: 0.9; margin-bottom: 5px; }
        .data-value { font-size: 1.1em; font-weight: 700; }
        .forecast-days { display: grid; gap: 20px; }
        .forecast-day { background: #f8f9fa; border-radius: 12px; padding: 20px; border: 1px solid #dee2e6; }
        .forecast-day-header { font-size: 1.2em; font-weight: 600; color: #333; margin-bottom: 15px; 
                              text-align: center; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        .forecast-hours { display: grid; grid-template-columns: repeat(auto-fill, minmax(60px, 1fr)); gap: 8px; }
        .forecast-hour { background: white; padding: 8px 4px; border-radius: 6px; text-align: center; 
                        border: 1px solid #e0e0e0; }
        .forecast-time { font-size: 0.7em; color: #666; margin-bottom: 3px; }
        .forecast-value { font-size: 0.9em; font-weight: 700; color: #667eea; }
        .forecast-unit { font-size: 0.6em; color: #999; }
        .no-data { color: #999; font-style: italic; text-align: center; padding: 40px; }
    </style>
    <script>
        function showTab(stationName) {
            // Ocultar todos los contenidos
            var contents = document.querySelectorAll('.tab-content');
            for(var i = 0; i < contents.length; i++) {
                contents[i].classList.remove('active');
            }
            
            // Desactivar todos los botones
            var buttons = document.querySelectorAll('.tab-button');
            for(var i = 0; i < buttons.length; i++) {
                buttons[i].classList.remove('active');
            }
            
            // Mostrar el contenido seleccionado
            document.getElementById(stationName).classList.add('active');
            
            // Activar el botón correspondiente
            var targetBtn = document.querySelector('[onclick="showTab(\\''+stationName+'\\')"]');
            if(targetBtn) targetBtn.classList.add('active');
        }
        
        // Mostrar la primera pestaña por defecto
        window.onload = function() {
            showTab('Badia');
        }
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌬️ Haize Iragarpena - Parke Eolikoak</h1>
            <div>Azken eguneratzea: ''' + timestamp + '''</div>
        </header>
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <strong>📊 Uneko Datuak:</strong> Simulazioan eskuragarri dagoen une hurbileneko informazioa
        </div>
        
        <div class="tabs-container">
            <div class="tabs-header">'''
    
    # Agregar botones de pestañas
    for park_name in parques_data.keys():
        head_content += f'<button class="tab-button" onclick="showTab(\'{park_name}\')">⚡ {park_name}</button>'
    
    head_content += '</div>'
    
    # Agregar contenido de cada pestaña
    for park_name, park_info in parques_data.items():
        head_content += f'<div id="{park_name}" class="tab-content">'
        
        # Datos actuales
        if park_info['has_data']:
            head_content += f'<div class="current-data"><h3>📊 Uneko Datuak - {park_info["fecha_ref"]}</h3><div class="data-grid">'
            for col, value in park_info['data'].items():
                if col not in ['timestamp', 'fechas', 'time_diff']:
                    head_content += f'<div class="data-item"><div class="data-label">{col}</div><div class="data-value">{value}</div></div>'
            head_content += '</div></div>'
        else:
            head_content += '<div class="no-data">Ez dago daturik eskuragarri data honetarako</div>'
        
        # Pronóstico
        if park_name in forecast_by_station and forecast_by_station[park_name]:
            head_content += '<div style="margin-top: 20px;"><h3>📈 5 eguneko iragarpena (24 ordu)</h3><div class="forecast-days">'
            for day_data in forecast_by_station[park_name]:
                head_content += f'<div class="forecast-day"><div class="forecast-day-header">{day_data["date"]} - {day_data["weekday"]}</div><div class="forecast-hours">'
                for hour_data in day_data['hours']:
                    head_content += f'<div class="forecast-hour"><div class="forecast-time">{hour_data["hour"]}</div><div class="forecast-value">{hour_data["wind_mps"]}</div><div class="forecast-unit">m/s</div></div>'
                head_content += '</div></div>'
            head_content += '</div></div>'
        else:
            head_content += '<div class="no-data">Ez dago iragarpen eskuragarririk estazio honetarako</div>'
        
        head_content += '</div>'
    
    head_content += '</div></div></body></html>'
    
    return head_content

# --- Main execution ---
def main():
    # Timestamp de ejecución
    madrid_tz = pytz.timezone('Europe/Madrid')
    timestamp = datetime.now(madrid_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    # Cargar datos
    parques = load_all_sheets(GSHEET_ID)
    
    # Procesar datos actuales de cada parque
    parques_data = {}
    for nombre, df in parques.items():
        df_sel, fecha_actual = get_current_data(df, fecha_col="timestamp")
        
        if not df_sel.empty:
            # Convertir la primera fila a diccionario
            data_dict = df_sel.iloc[0].to_dict()
            parques_data[nombre] = {
                'has_data': True,
                'fecha_ref': fecha_actual.strftime('%Y-%m-%d %H:%M'),
                'data': data_dict
            }
        else:
            parques_data[nombre] = {
                'has_data': False,
                'fecha_ref': None,
                'data': {}
            }
    
    # Obtener pronósticos reales del sheet por estación
    forecast_by_station = {}
    for nombre, df in parques.items():
        forecast = get_forecast_from_sheet(df, fecha_col="timestamp")
        forecast_by_station[nombre] = forecast
    
    # Generar HTML
    html_content = generate_html(parques_data, forecast_by_station, timestamp)
    
    # Guardar archivo
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTMLa arrakastaz sortu da: index.html")
    print(f"📅 Data-ordua: {timestamp}")
    print(f"📊 Benetako iragarpena lortu da sheet-etik {len(forecast_by_station)} estazioetarako")

if __name__ == "__main__":
    main()
