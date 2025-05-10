import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import os

@st.cache_data
def load_data(file_path, key_column=None):
    df = pd.read_csv(file_path)

    columns_to_keep = []
    if '施設・場所名' in df.columns:
        columns_to_keep.append('施設・場所名')
    if '住所' in df.columns:
        columns_to_keep.append('住所')
    if '緯度' in df.columns:
        columns_to_keep.append('緯度')
    if '経度' in df.columns:
        columns_to_keep.append('経度')
    if '地震' in df.columns:
        columns_to_keep.append('地震')
    if '津波' in df.columns:
        columns_to_keep.append('津波')
    if '洪水水害' in df.columns:
        columns_to_keep.append('洪水水害')
    if '土砂災害' in df.columns:
        columns_to_keep.append('土砂災害')
    if key_column and key_column in df.columns:
        columns_to_keep.append(key_column)

    return df[columns_to_keep]

@st.cache_data
def find_nearest_shelters(df, lat, lon, filter_column=None, filter_value=None, top_n=5):
    df['距離(km)'] = df.apply(
        lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1
    )
    filtered_df = df
    if filter_column and filter_value:
        filtered_df = df[df[filter_column] == filter_value]
    return filtered_df.sort_values(by='距離(km)').head(top_n)

def plot_on_map(current_lat, current_lon, nearest_shelters):
    m = folium.Map(
        location=[current_lat, current_lon],
        zoom_start=14,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps"
    )

    folium.Marker(
        location=[current_lat, current_lon],
        popup=folium.Popup("<b>現在位置</b>", max_width=300),
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    for _, row in nearest_shelters.iterrows():
        distance_km = row['距離(km)']
        marker_color = "darkgreen" if distance_km < 0.5 else "darkblue" if distance_km < 1.0 else "lightgray"
        popup_content = f"<b>{row['施設・場所名']}</b><br>距離: {distance_km:.1f} km<br>"
        folium.Marker(
            location=[row['緯度'], row['経度']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)

    return m

def save_map_as_html(map_object, file_name="map.html"):
    map_object.save(file_name)
    return file_name

def main():
    st.markdown("<h1 style='font-size:26px;'>避難所検索アプリ Ver 0.2（災害別絞込み対応）</h1>", unsafe_allow_html=True)
    
    try:
        # CSVファイル（国 + 自治体照合済）のパス
        file_path1 = "38213_1.csv"
        file_path2 = "自治体_避難所一覧_照合済_20250511_0801.csv"

        df1 = load_data(file_path1, key_column="共通ID")
        df2 = load_data(file_path2, key_column="共通ID")
        combined_df = pd.merge(df1, df2, on="共通ID", how="left")

        # 災害条件：列名を実データに対応
        disaster_options = ["地震", "津波", "洪水", "土砂"]
        selected_disaster = st.selectbox("対応災害を選択", disaster_options)
        status_options = ["O", "A", "X"]
        selected_status = st.selectbox("対応状況を選択", status_options)

        disaster_columns = {
            "地震": "地震",
            "津波": "津波",
            "洪水": "洪水水害",
            "土砂": "土砂災害"
        }
        filter_column = disaster_columns.get(selected_disaster)

        user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.8116, 132.7788）:")

        if not user_input:
            st.info("緯度・経度を入力してください。")
            return

        lat, lon = map(float, user_input.strip().strip('()').replace(" ", "").split(","))
        nearest_shelters = find_nearest_shelters(
            combined_df, lat, lon, filter_column=filter_column, filter_value=selected_status, top_n=5
        )

        if nearest_shelters.empty:
            st.warning("該当する避難所が見つかりませんでした。")
            return

        st.subheader("最も近い避難所一覧")
        display_columns = [
            '施設・場所名', '距離(km)', '地震', '津波',
            '洪水水害', '土砂災害', '共通ID'
        ]
        st.table(nearest_shelters[display_columns])

        map_object = plot_on_map(lat, lon, nearest_shelters)
        saved_file = save_map_as_html(map_object, file_name="nearest_shelters_map.html")

        st.subheader("地図表示")
        st_folium(map_object, width=700, height=500)

        with open(saved_file, "rb") as f:
            st.download_button("地図をHTMLファイルとしてダウンロード", data=f, file_name=os.path.basename(saved_file), mime="text/html")

    except ValueError as ve:
        st.error(f"入力エラー: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

if __name__ == "__main__":
    main()
