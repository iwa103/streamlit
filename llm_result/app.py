import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Scores by Model and Mode (Grouped by Subject)")

# --- Load CSV from GitHub
CSV_URL = "llm_result/log_summary_by_model_mode_total.csv"
df = pd.read_csv(CSV_URL)
df = df[df["科目"] != "合計"]
df = df.fillna(0)

# --- Map Japanese subject names to English
subject_map = {
    "一般常識": "General Knowledge",
    "地理": "Geography",
    "数学": "Mathematics",
    "SPI": "SPI"
}
df["Subject_EN"] = df["科目"].map(subject_map).fillna(df["科目"])

# --- Create ModelID and display label
df["ModelID"] = df["モデル"] + " (" + df["パラメータサイズ"].astype(str) + "B)"
df["Label"] = df["ModelID"] + "\n[" + df["モード"] + "]"

# --- Desired model display order
model_bases = [
    "llm-jp", "qwen3", "qwq", "GPT4o",
    "qwen2.5", "qwen2.5 ts", "gemma3", "Llama 3.1", "Llama 3.2"
]
model_order = []
for base in model_bases:
    candidates = df[df["モデル"].fillna("").str.startswith(base)]
    sizes = sorted(candidates["パラメータサイズ"].unique())
    for size in sizes:
        matched = candidates[candidates["パラメータサイズ"] == size]["モデル"].unique()
        for m in matched:
            model_order.append(f"{m} ({size}B)")

# ✅ Remove duplicates while preserving order
model_order = list(dict.fromkeys(model_order))

# --- Apply categorical order
df["ModelID"] = pd.Categorical(df["ModelID"], categories=model_order, ordered=True)
df = df.sort_values(["ModelID", "モード"])

# --- Assign color by model type
def assign_color(row):
    model = row["モデル"]
    if model.startswith("llm-jp"):
        return "#4A90E2"
    elif model.startswith("qwen3"):
        return "#E74C3C" if row["モード"] == "no_think" else "#F39C12"
    elif model.startswith("qwq"):
        return "#27AE60"
    elif model.startswith("GPT4o"):
        return "#7F8C8D"
    elif model.startswith("qwen2.5 ts"):
        return "#D35400"
    elif model.startswith("qwen2.5"):
        return "#9B59B6"
    elif model.startswith("gemma3"):
        return "#16A085"
    elif model.startswith("Llama 3.1"):
        return "#2980B9"
    elif model.startswith("Llama 3.2"):
        return "#1ABC9C"
    return "gray"

df["Color"] = df.apply(assign_color, axis=1)

# --- Sidebar filters
model_id_list = df["ModelID"].cat.categories.tolist()
selected_models = st.sidebar.multiselect("Select models", model_id_list, default=model_id_list)

mode_list = sorted(df["モード"].unique())
selected_modes = st.sidebar.multiselect("Select modes", mode_list, default=mode_list)

# --- Filtered data
filtered_df = df[(df["ModelID"].isin(selected_models)) & (df["モード"].isin(selected_modes))]

# --- Fixed subject order
subject_order = ["General Knowledge", "Geography", "Mathematics", "SPI"]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
else:
    for subject in subject_order:
        if subject not in filtered_df["Subject_EN"].values:
            continue

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
