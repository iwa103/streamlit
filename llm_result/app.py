import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# Optional: remove any font override to avoid issues
# matplotlib.rcParams['font.family'] = 'sans-serif'

st.title("Scores by Model and Mode (Grouped by Subject)")

# --- Load CSV from GitHub URL
CSV_URL = "llm_result/log_summary_by_model_mode_total.csv"
df = pd.read_csv(CSV_URL)
df = df[df["科目"] != "合計"]

# --- Map subject names from Japanese to English
subject_map = {
    "一般常識": "General Knowledge",
    "地理": "Geography",
    "数学": "Mathematics",
    "SPI": "SPI"
}
df["Subject_EN"] = df["科目"].map(subject_map).fillna(df["科目"])

# --- Create model ID and display label
df["ModelID"] = df["モデル"] + " (" + df["パラメータサイズ"].astype(str) + "B)"
df["Label"] = df["ModelID"] + "\n[" + df["モード"] + "]"

# --- Manual model sort: llm-jp → qwen3 → qwq (sorted by size)
model_order = []
model_bases = ["llm-jp", "qwen3", "qwq"]
for base in model_bases:
    candidates = df[df["モデル"].str.startswith(base)]
    sizes = sorted(candidates["パラメータサイズ"].unique())
    for size in sizes:
        matched_models = candidates[candidates["パラメータサイズ"] == size]["モデル"].unique()
        for model_name in matched_models:
            model_order.append(f"{model_name} ({size}B)")

df["ModelID"] = pd.Categorical(df["ModelID"], categories=model_order, ordered=True)
df = df.sort_values(["ModelID", "モード"])

# --- Color assignment
def assign_color(row):
    if row["モデル"].startswith("llm-jp"):
        return "#4A90E2"  # Blue
    elif row["モデル"].startswith("qwen3"):
        return "#E74C3C" if row["モード"] == "no_think" else "#F39C12"  # Red / Orange
    elif row["モデル"].startswith("qwq"):
        return "#27AE60"  # Green
    return "gray"

df["Color"] = df.apply(assign_color, axis=1)

# --- Sidebar filters
model_id_list = df["ModelID"].cat.categories.tolist()
selected_models = st.sidebar.multiselect("Select models", model_id_list, default=model_id_list)

mode_list = sorted(df["モード"].unique())
selected_modes = st.sidebar.multiselect("Select modes", mode_list, default=mode_list)

# --- Filtered data
filtered_df = df[(df["ModelID"].isin(selected_models)) & (df["モード"].isin(selected_modes))]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
else:
    for subject in filtered_df["Subject_EN"].unique():
        st.subheader(f"[{subject}]")

        sub_df = filtered_df[filtered_df["Subject_EN"] == subject]

        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.bar(sub_df["Label"], sub_df["スコア"], color=sub_df["Color"])

        ax.set_ylabel("Score")
        ax.set_xlabel("Model (Mode)")
        ax.set_title(f"{subject}: Score by Model")
        ax.set_ylim(0, 105)
        ax.set_xticks(range(len(sub_df)))
        ax.set_xticklabels(sub_df["Label"], rotation=45, ha="right")

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1, f"{height:.1f}", ha='center', va='bottom')

        st.pyplot(fig)
