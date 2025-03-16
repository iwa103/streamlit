import pandas as pd
import streamlit as st
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import os

# CSVファイルからデータを読み込む関数
@st.cache_data
def load_data(file_path, key_column=None):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)

    # 必要な列を保持
    columns_to_keep = []
    if '施設・場所名' in df.columns:
        columns_to_keep.append('施設・場所名')
    if '住所' in df.columns:
        columns_to_keep.append('住所')
    if '緯度' in df.columns:
        columns_to_keep.append('緯度')
    if '経度' in df.columns:
        columns_to_keep.append('経度')
    if 'df2_地震' in df.columns:
        columns_to_keep.append('df2_地震')
    if 'df2_津波' in df.columns:
        columns_to_keep.append('df2_津波')
    if 'df2_高潮' in df.columns:
        columns_to_keep.append('df2_高潮')
    if 'df2_洪水' in df.columns:
        columns_to_keep.append('df2_洪水')
    if 'df2_土砂' in df.columns:
        columns_to_keep.append('df2_土砂')

    if key_column and key_column in df.columns:
        columns_to_keep.append(key_column)  # キー列も保持

    # 必要な列のみを残す
    df_filtered = df[columns_to_keep]

    return df_filtered

# 最も近い避難所を検索する関数
@st.cache_data
def find_nearest_shelters(df, lat, lon, filter_column=None, filter_value=None, top_n=5):
    # 現在地からの距離を計算
    df['距離(km)'] = df.apply(
        lambda row: geodesic((lat, lon), (row['緯度'], row['経度'])).km, axis=1
    )

    # 条件によるフィルタリング
    if filter_column and filter_value:
        filtered_df = df[df[filter_column] == filter_value]
    else:
        filtered_df = df

    # 距離が近い順にソートし、上位N件を取得
    return filtered_df.sort_values(by='距離(km)').head(top_n)

# 地図を生成する関数
def plot_on_map(current_lat, current_lon, nearest_shelters):
    # 地図の中心を現在位置に設定
    map_center = [current_lat, current_lon]
    m = folium.Map(location=map_center, zoom_start=14, tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google Maps")

    # 現在位置を赤いマーカーで表示
    folium.Marker(
        location=[current_lat, current_lon],
        popup=folium.Popup("<b>現在位置</b>", max_width=300),  # 変更点：HTML形式でポップアップを指定,
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    # 避難所をマーカーで表示
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

# 地図をHTMLファイルとして保存する関数
def save_map_as_html(map_object, file_name="map.html"):
    map_object.save(file_name)
    return file_name


# Streamlitアプリのメイン処理
def main():
    # st.title("避難所検索アプリ（災害種別対応版　松山市のみ）")

    st.markdown("""
    <div style='text-align: center; line-height: 1.0;'>
        <h2>避難所検索アプリ</h2>
        <h2>災害対応種別対応版</h2>
        <h2>対象地域　松山市</h2>
    </div>
    """, unsafe_allow_html=True)

    try:
        # CSVファイルを読み込み
        file_path1 = "mergeFromCity_1.csv"  # DF1
        file_path2 = "matsu_hinan.csv"     # DF2

        # データを前処理（それぞれのキー列を指定）
        df1 = load_data(file_path1, key_column="共通ID")
        df2 = load_data(file_path2, key_column="共通ID")

        # キー列の名前を統一して結合
        combined_df = pd.merge(df1, df2, on="共通ID", how="left")

        # 災害の選択
        disaster_options = ["地震", "津波", "高潮", "洪水", "土砂"]
        selected_disaster = st.selectbox("対応災害を選択", disaster_options)

        # 対応状況の選択
        status_options = ["○", "△", "✕"]
        selected_status = st.selectbox("対応状況を選択", status_options)

        # 災害に対応する列名を決定
        disaster_columns = {
            "地震": "df2_地震",
            "津波": "df2_津波",
            "高潮": "df2_高潮",
            "洪水": "df2_洪水",
            "土砂": "df2_土砂"
        }
        filter_column = disaster_columns.get(selected_disaster)
        filter_value = selected_status

        # 現在位置の入力
        user_input = st.text_input("現在位置の緯度・経度を入力してください（例: 33.81167462685436, 132.77887072795122）:")

        # 入力フォーマットの正規化
        if not user_input:
            st.info("緯度・経度を入力してください。")
            return

        user_input = user_input.strip().strip('()').replace(" ", "")  # 前後の空白やカッコを削除
        lat, lon = map(float, user_input.split(","))  # 緯度と経度を分割して数値に変換

        # 最も近い避難所を検索
        nearest_shelters = find_nearest_shelters(
            combined_df,
            lat,
            lon,
            filter_column=filter_column,  # 災害に対応する列名
            filter_value=filter_value,    # 対応状況
            top_n=5
        )

        # 条件に一致する避難所がない場合の警告
        if len(nearest_shelters) == 0:
            st.warning(f"'{selected_disaster}' の '{selected_status}' に一致する避難所が見つかりませんでした。")
            return

        # 結果をテーブルで表示
        st.subheader("最も近い避難所一覧")
        display_columns = ['施設・場所名', '距離(km)', 'df2_地震', 'df2_津波', 'df2_高潮', 'df2_洪水', 'df2_土砂', '共通ID']
        nearest_shelters_display = nearest_shelters[display_columns]
        st.table(nearest_shelters_display)

        # 地図を生成
        map_object = plot_on_map(lat, lon, nearest_shelters)

        # 地図をHTMLファイルとして保存
        saved_file = save_map_as_html(map_object, file_name="nearest_shelters_map.html")

        # 地図をStreamlitで表示
        st.subheader("地図表示")
        st_folium(map_object, width=700, height=500)

        # HTMLファイルをダウンロード可能にする
        with open(saved_file, "rb") as f:
            st.download_button(
                label="地図をHTMLファイルとしてダウンロード",
                data=f,
                file_name=os.path.basename(saved_file),
                mime="text/html"
            )


    except ValueError as ve:
        st.error(f"エラーが発生しました: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()