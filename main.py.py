import streamlit as st
import requests
import pandas as pd
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from streamlit_folium import st_folium
import folium

# --- 1. 定数・設定 ---
WEATHER_ICONS = {
    0: "☀️ 晴天", 1: "🌤️ 晴れ", 2: "⛅ 曇りがち", 3: "☁️ 曇り",
    45: "🌫️ 霧", 48: "🌫️ 霧",
    51: "🌦️ 小雨", 53: "🌦️ 小雨", 55: "🌧️ 雨",
    61: "🌧️ 雨", 63: "🌧️ 雨", 65: "🌧️ 強い雨",
    71: "❄️ 雪", 73: "❄️ 雪", 75: "❄️ 強い雪",
    80: "🌦️ にわか雨", 81: "🌧️ にわか雨", 82: "⛈️ 激しい雨",
}

# --- 2. データ取得関数 ---
def get_weather(lat, lon, date_obj):
    date_str = date_obj.strftime('%Y-%m-%d')
    # 日付によって窓口を自動切り替え
    if date_obj < datetime.now() - timedelta(days=2):
        url = "https://archive-api.open-meteo.com/v1/archive"
    else:
        url = "https://api.open-meteo.com/v1/forecast"
        
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["temperature_2m", "precipitation", "weather_code"],
        "start_date": date_str, "end_date": date_str, "timezone": "Asia/Tokyo"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "hourly" not in data: return None
        df = pd.DataFrame({
            "時間": [t.split("T")[1] for t in data["hourly"]["time"]],
            "気温(℃)": data["hourly"]["temperature_2m"],
            "降水(mm)": data["hourly"]["precipitation"],
            "状態コード": data["hourly"]["weather_code"]
        })
        df["天気"] = df["状態コード"].map(lambda x: WEATHER_ICONS.get(x, "❓ 不明"))
        return df
    except: return None

def get_lat_lon(city_name):
    try:
        geolocator = Nominatim(user_agent="weather_app_v9")
        location = geolocator.geocode(city_name)
        return (location.latitude, location.longitude) if location else (None, None)
    except: return None, None

# --- 3. UI表示設定 ---
st.set_page_config(page_title="Weather Pro Pro", layout="wide")

st.markdown("""
    <style>
    .weather-card {
        background-color: #ffffff !important;
        padding: 15px; border-radius: 12px; text-align: center;
        border: 2px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        min-height: 160px;
    }
    .card-time { font-size: 0.9em; color: #555555 !important; }
    .card-icon { font-size: 2.2em; margin: 10px 0; }
    .card-temp { font-size: 1.3em; font-weight: bold; color: #000000 !important; }
    .card-label { font-size: 0.85em; font-weight: bold; color: #333333 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🗺️ AI気象アナリスト：比較機能強化版")

with st.sidebar:
    st.header("📅 日付設定")
    this_year = datetime.now().year
    sel_year = st.selectbox("年", list(range(this_year, 1950, -1)))
    sel_month = st.selectbox("月", list(range(1, 13)), index=datetime.now().month - 1)
    sel_day = st.selectbox("日", list(range(1, 32)), index=min(datetime.now().day - 1, 30))
    try:
        selected_date = datetime(sel_year, sel_month, sel_day)
    except ValueError:
        st.error("存在しない日付です。")
        st.stop()
    
    st.divider()
    st.header("🔍 場所の選択")
    method = st.radio("選択方法", ["地図でタップ", "都市名入力"])
    target_lat, target_lon = None, None
    if method == "都市名入力":
        city = st.text_input("都市名", "茨城")
        target_lat, target_lon = get_lat_lon(city)
    else:
        st.info("地図をクリックしてください")

# 地図表示
if method == "地図でタップ":
    m = folium.Map(location=[35.68, 139.76], zoom_start=5)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=350, width='100%')
    if map_data and map_data.get("last_clicked"):
        target_lat = map_data["last_clicked"]["lat"]
        target_lon = map_data["last_clicked"]["lng"]

# データ表示
if target_lat and target_lon:
    st.success(f"📍 選択地点: 北緯{target_lat:.2f}, 東経{target_lon:.2f}")

    # 昨日・明日データの取得
    df_yest = get_weather(target_lat, target_lon, selected_date - timedelta(days=1))
    df_tomm = get_weather(target_lat, target_lon, selected_date + timedelta(days=1))
    
    st.subheader("🔄 前後比較（最高 / 最低）")
    c1, c2 = st.columns(2)
    
    if df_yest is not None:
        with c1:
            # 最高・最低気温を抽出
            max_t = df_yest["気温(℃)"].max()
            min_t = df_yest["気温(℃)"].min()
            weather_main = df_yest["天気"].mode()[0]
            # 赤枠部分の表示を修正
            st.metric(f"📅 前日 ({ (selected_date - timedelta(days=1)).strftime('%m/%d') })", 
                      f"{max_t}℃ / {min_t}℃", 
                      f"天気: {weather_main}", delta_color="off")
            
    if df_tomm is not None:
        with c2:
            max_t = df_tomm["気温(℃)"].max()
            min_t = df_tomm["気温(℃)"].min()
            weather_main = df_tomm["天気"].mode()[0]
            st.metric(f"📅 翌日 ({ (selected_date + timedelta(days=1)).strftime('%m/%d') })", 
                      f"{max_t}℃ / {min_t}℃", 
                      f"天気: {weather_main}", delta_color="off")

    # 当日の詳細表示
    st.divider()
    df_current = get_weather(target_lat, target_lon, selected_date)
    if df_current is not None:
        st.subheader(f"📊 {selected_date.strftime('%Y-%m-%d')} の詳細")
        target_hours = [0, 3, 6, 9, 12, 15, 18, 21]
        cols = st.columns(len(target_hours))
        for i, h_idx in enumerate(target_hours):
            row = df_current.iloc[h_idx]
            with cols[i]:
                icon = row['天気'].split()[0]
                label = row['天気'].split()[1]
                st.markdown(f"""
                    <div class="weather-card">
                        <div class="card-time">{row['時間']}</div>
                        <div class="card-icon">{icon}</div>
                        <div class="card-temp">{row['気温(℃)']}°</div>
                        <div class="card-label">{label}</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        st.line_chart(df_current.set_index("時間")["気温(℃)"])
else:
    if method == "地図でタップ":
        st.warning("地図をクリックして場所を指定してください。")