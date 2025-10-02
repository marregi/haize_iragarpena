import pandas as pd
from datetime import datetime, timedelta
import json

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

# --- Generar HTML ---
def generate_html(parques_data, forecast_data, timestamp):
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
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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
            font-size: 2em;
            font-weight: 600;
            color: #333;
        }}
        
        .forecast-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }}
        
        .forecast-day {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
            transition: transform 0.3s ease;
        }}
        
        .forecast-day:hover {{
            transform: scale(1.05);
        }}
        
        .forecast-date {{
            font-size: 0.9em;
            margin-bottom: 10px;
            opacity: 0.9;
        }}
        
        .forecast-value {{
            font-size: 2em;
            font-weight: 700;
            margin: 10px 0;
        }}
        
        .forecast-unit {{
            font-size: 0.8em;
            opacity: 0.8;
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
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
        
        html += """
            </div>
"""
    
    # Sección de pronóstico
    html += """
        </div>
        
        <div class="forecast-section">
            <div class="forecast-header">
                <span style="font-size: 2em;">📈</span>
                <span class="forecast-title">Pronóstico 5 Días</span>
            </div>
            <div class="forecast-grid">
"""
    
    if forecast_data is not None and not forecast_data.empty:
        for _, row in forecast_data.iterrows():
            fecha_str = row['fecha'].strftime('%d/%m/%Y')
            wind_value = row['wind_mps_pronostico']
            html += f"""
                <div class="forecast-day">
                    <div class="forecast-date">{fecha_str}</div>
                    <div class="forecast-value">{wind_value}</div>
                    <div class="forecast-unit">m/s</div>
                </div>
"""
    else:
        html += """
                <div class="no-data">
                    No hay pronóstico disponible
                </div>
"""
    
    html += """
            </div>
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
    
    # Generar pronóstico
    df_total = []
    for nombre, df in parques.items():
        if {"fechas", "wind_mps"}.issubset(df.columns):
            df["fechas"] = pd.to_datetime(df["fechas"], errors="coerce")
            df_total.append(df[["fechas", "wind_mps"]])
    
    df_forecast = None
    if df_total:
        df_total = pd.concat(df_total).dropna().sort_values("fechas")
        ult_fecha = df_total["fechas"].max()
        fechas_futuras = pd.date_range(ult_fecha + pd.Timedelta(days=1), periods=5, freq="D")
        promedio = df_total[df_total["fechas"] > (ult_fecha - pd.Timedelta(days=30))]["wind_mps"].mean()
        pronostico = [round(promedio, 2)] * 5
        df_forecast = pd.DataFrame({
            "fecha": fechas_futuras,
            "wind_mps_pronostico": pronostico
        })
    
    # Generar HTML
    html_content = generate_html(parques_data, df_forecast, timestamp)
    
    # Guardar archivo
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML generado exitosamente: index.html")
    print(f"📅 Timestamp: {timestamp}")

if __name__ == "__main__":
    main()
