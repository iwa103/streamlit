import pandas as pd
import streamlit as st

# CSVファイルからデータを読み込む関数
@st.cache_data
def load_data(file_path):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path)
    return df

# Streamlitアプリのメイン処理
def main():
    st.title("CSVファイルのデータ結合")

    try:
        # 2つのCSVファイルを読み込み
        file_path1 = "mergeFromCity_1.csv"  # DF1
        file_path2 = "matsu_hinan.csv"     # DF2

        # データを読み込む
        df1 = load_data(file_path1)
        df2 = load_data(file_path2)

        # 必要な列が存在することを確認
        required_columns_df1 = ['施設・場所名', '住所', '緯度', '経度', '共通ID']
        required_columns_df2 = ['df2_地震', 'df2_共通ID']

        missing_columns_df1 = [col for col in required_columns_df1 if col not in df1.columns]
        missing_columns_df2 = [col for col in required_columns_df2 if col not in df2.columns]

        if missing_columns_df1:
            raise ValueError(f"DF1に次の必要な列が見つかりません: {missing_columns_df1}")
        if missing_columns_df2:
            raise ValueError(f"DF2に次の必要な列が見つかりません: {missing_columns_df2}")

        # 左結合でDF2のデータをDF1に追加
        df3 = pd.merge(df1, df2, on="共通ID", how="left")

        # 結合結果を確認
        st.subheader("結合されたデータ (DF3)")
        st.write(df3)

    except ValueError as ve:
        st.error(f"エラーが発生しました: {ve}")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()