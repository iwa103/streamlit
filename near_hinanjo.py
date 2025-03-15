import pandas as pd
import folium
from geopy.distance import geodesic
import streamlit as st
from streamlit_folium import st_folium

# CSVファイルからデータを読み込み、「要配慮者」の行を除外する関数
@st.cache_data
def load_and_preprocess_data(file_path):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)

    # 「受入対象者」列に「要配慮者」と書かれている行を除外
    df_filtered = df[df['受入対象者'] != '要配慮者']

    # 必要な列のみを残す（オプション）
    columns_to_keep = ['施設・場所名', '住所', '緯度', '経度']
    df_filtered = df_filtered[columns_to_keep]

    return df_filtered

# 地図を生成する関数
def plot_on_map(current_lat, current_lon, nearest_shelters):
    # 地図の中心を現在位置に設定
    map_center = [current_lat, current_lon]
    m = folium.Map(location=map_center, zoom_start=14, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps")

    # 現在位置を赤いマーカーで表示
    folium.Marker(
        location=[current_lat, current_lon],
        popup="現在位置",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # 避難所をマーカーで表示
    for _, row in nearest_shelters.iterrows():
        distance_km = row['距離(km)']
        marker_color = "green" if distance_km < 0.5 else "darkblue" if distance_km < 1.0 else "lightgray"
        popup_content = f"<b>{row['施設・場所名']}</b><br>距離: {distance_km:.1f} km<br>"
        folium.Marker(
            location=[row['緯度'], row['経度']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)

    return m

# 最も近い避難所を検索する関数
@st.cache_data
def find_nearest_shelters(df, lat, lon, top_n=5):
    df['距離(km)'] = df.apply(lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1)
    return df.sort_values(by='距離(km)').head(top_n)

# Streamlitアプリのメイン処理
def main():
    st.title("避難所検索アプリ")

    # 現在位置の入力
    user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")
    
    try:
        # 入力フォーマットの正規化
        if not user_input:
            st.info("緯度・経度を入力してください。")
            return
        
        user_input = user_input.strip()  # 前後の空白を削除
        user_input = user_input.strip('()')  # カッコを削除
        user_input = user_input.replace(" ", "")  # スペースを削除

        # 緯度と経度を分割して数値に変換
        lat, lon = map(float, user_input.split(","))

        # 避難所データを読み込む（「要配慮者」を除外）
        file_path = "mergeFromCity_1.csv"  # CSVファイルのパス
        df = load_and_preprocess_data(file_path)

        # 最も近い避難所を検索（上位5つ）
        nearest_shelters = find_nearest_shelters(df, lat, lon, top_n=5)

        # 結果をテーブルで表示
        st.subheader("最も近い避難所一覧")
        nearest_shelters_display = nearest_shelters[['施設・場所名', '距離(km)']]
        st.table(nearest_shelters_display)

        # 地図を生成して表示
        map_object = plot_on_map(lat, lon, nearest_shelters)
        st_folium(map_object, width=700, height=500)

    except ValueError:
        st.error("入力が正しくありません。緯度と経度をカンマ区切りで入力してください（例: 33.81167462685436, 132.77887072795122）。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()