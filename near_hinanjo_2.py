import pandas as pd
import folium
from geopy.distance import geodesic
import streamlit as st
from streamlit_folium import st_folium
import os

# CSVファイルからデータを読み込み、「要配慮者」の行を除外する関数
@st.cache_data
def load_and_preprocess_data(file_path, key_column=None):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)

    # 必要な列が存在するか確認
    required_columns = ['施設・場所名', '住所', '緯度', '経度']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"次の必要な列が見つかりません: {missing_columns}")

    # 「受入対象者」列に「要配慮者」と書かれている行を除外
    if '受入対象者' in df.columns:
        df_filtered = df[df['受入対象者'] != '要配慮者']
    else:
        df_filtered = df  # 「受入対象者」列がない場合、そのまま使用

    # 必要な列のみを残す（オプション）
    columns_to_keep = required_columns.copy()
    if key_column and key_column in df_filtered.columns:
        columns_to_keep.append(key_column)  # キー列も保持
    if 'df2_地区名' in df_filtered.columns:  # 追加で確認用の列を保持
        columns_to_keep.append('df2_地区名')
    df_filtered = df_filtered[columns_to_keep]

    return df_filtered

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

        # 2つのCSVファイルを読み込み
        file_path1 = "mergeFromCity_1.csv"  # 1つ目のCSVファイル
        file_path2 = "matsu_hinan.csv"     # 2つ目のCSVファイル

        # データを前処理（それぞれのキー列を指定）
        df1 = load_and_preprocess_data(file_path1, key_column="共通ID")
        df2 = load_and_preprocess_data(file_path2, key_column="df2_共通ID")

        # キー列の名前を統一してマージ
        df2 = df2.rename(columns={"df2_共通ID": "共通ID"})  # 列名を統一
        combined_df = pd.merge(df1, df2, on="共通ID", how="outer")

        # マージ結果を確認
        st.subheader("マージされたデータ")
        st.write(combined_df)

        # 最も近い避難所を検索（上位5つ）
        nearest_shelters = find_nearest_shelters(combined_df, lat, lon, top_n=5)

        # 結果をテーブルで表示
        st.subheader("最も近い避難所一覧")
        display_columns = ['施設・場所名', '距離(km)', 'df2_地区名', '共通ID']
        nearest_shelters_display = nearest_shelters[display_columns]
        st.table(nearest_shelters_display)

        # 地図を生成
        map_object = plot_on_map(lat, lon, nearest_shelters)

        # 地図をHTMLファイルとして保存
        saved_file = save_map_as_html(map_object, file_name="nearest_shelters_map.html")

        # 地図をStreamlitで表示
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