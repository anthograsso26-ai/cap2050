import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path


st.set_page_config(page_title="Slider Predictor", page_icon="📈", layout="wide")
@st.cache_data
def load_dataset(path: str):
    df = pd.read_csv(path)
    key_cols = ["croissance", "reduction", "gain"]
    year_cols = [c for c in df.columns if c not in key_cols]
    year_cols = [str(int(float(c))) for c in year_cols]
    year_cols = sorted(year_cols, key=int)
    years_int = [int(y) for y in year_cols]
    return df, year_cols, years_int

@st.cache_data
def omi_table(years_int):
    OMI_KNOWN = {
        2025:1.0, 2026:0.988235, 2027:0.976471, 2028:0.964706, 2029:0.952941, 2030:0.941176,
        2031:0.882353, 2032:0.823529, 2033:0.764706, 2034:0.705882, 2035:0.647059, 2036:0.588235,
        2037:0.529412, 2038:0.470588, 2039:0.411765, 2040:0.352941, 2041:0.317647, 2042:0.282353,
        2043:0.247059, 2044:0.211765, 2045:0.176471, 2046:0.141176, 2047:0.105882, 2048:0.070588,
        2049:0.035294, 2050:0.0
    }
    return pd.DataFrame({
        "year": years_int,
        "value": [OMI_KNOWN.get(y, 0.0) for y in years_int],
        "series": "Objectif OMI"
    })

# use them
df, year_cols, years_int = load_dataset("complete_dataset.csv")
omi_df = omi_table(years_int)

def fmt_pct(x, decimals=1):
    """Return EU-style percent label, e.g., 2,5 %"""
    s = f"{x:.{decimals}f}".replace(".", ",")
    return f"{s} %"

def make_options(vmin, vmax, step, decimals=1):
    """Generate numeric option list with stable rounding for select_slider."""
    n = int(round((vmax - vmin) / step)) + 1
    vals = [round(vmin + i * step, decimals) for i in range(n)]
    return vals
# ---------- Page config ----------

st.markdown(
    """
    <div style="display:flex; align-items:center; justify-content:flex-start;">
        <a href="https://meet2050.org/" target="_blank" style="
            background-color:#0078D4;
            color:white;
            padding:0.4em 0.9em;
            border-radius:0.4em;
            text-decoration:none;
            font-weight:500;">
            🌐 Retour sur le site MEET2050
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
st.title("Exemple d'utilisation de l'outil CAP2050")

# --- Intro text (full width, between title and image)
st.markdown(
    """
**Cette mini-application** vous donne la possibilité de manipuler un modèle très simplifié de décarbonation du maritime — comme le permet l’outil **CAP2050** avec un plus grand nombre de paramètres et de données analysées.  
Modifiez les paramètres du modèle, via les curseurs, et constatez les effets sur les évolutions des émissions **(courbe bleue)** et leur position par rapport aux objectifs de décarbonation de l’**OMI** **(courbe rouge)**.

- Le paramètre **« Croissance de transport »** représente l’évolution de la demande en transport maritime ;
- Le paramètre **« Optimisation des opérations »** représente les différentes mesures d’efficacité opérationnelle — dont la réduction de vitesse de navigation et des temps d’attente ;
- Le paramètre **« Gains d’efficacité »** représente l’apport des innovations en efficacité énergétique.

Chacun de ces paramètres influence l’évolution des émissions, représentées ici par rapport à une année de référence **(2025, valeur de référence 100 %)**, et comptées en **« Well-to-Wake »**, c’est-à-dire sur l’ensemble du cycle d’exploitation des navires et des carburants.
    """
)

# ===================== ROW 1: Image only =====================
img_left, img_right = st.columns([1, 1.8], gap="large")
with img_left:
    APP_DIR = Path(__file__).resolve().parent
    IMAGE_SRC = APP_DIR / "MEET2050_image.jpeg"
    if IMAGE_SRC.exists():
        st.image(str(IMAGE_SRC), use_container_width=True)
    else:
        st.error(f"Image not found at: {IMAGE_SRC}")

# (Right column intentionally left empty so Row 2 starts below the image)

# ===================== ROW 2: Params (left) & Chart (right) == 
left, right = st.columns([1, 1.8], gap="large")

with left:
    st.subheader("🎚️ Paramètres")

    # Sliders
    c_opts = make_options(-2.0, 5.0, 0.5, decimals=1)
    r_opts = make_options(0.0, 25.0, 2.5, decimals=1)
    g_opts = make_options(0.0, 5.0, 0.5, decimals=1)

    c = st.select_slider(
        "Croissance de transport",
        options=c_opts,
        value=0.0,
        format_func=lambda v: fmt_pct(v, 1),
    )
    r = st.select_slider(
        "Optimisation des opérations",
        options=r_opts,
        value=0.0,
        format_func=lambda v: fmt_pct(v, 1),
    )
    g = st.select_slider(
        "Gains d’efficacité",
        options=g_opts,
        value=0.0,
        format_func=lambda v: fmt_pct(v, 1),
    )

# ---------- Data + computation ----------
df, year_cols, years_int = load_dataset("complete_dataset.csv")
omi_df = omi_table(years_int)

key_cols = ["croissance", "reduction", "gain"]
year_cols = [c for c in df.columns if c not in key_cols]
year_cols = [str(int(float(c))) for c in year_cols]
year_cols = sorted(year_cols, key=int)
years_int = [int(y) for y in year_cols]

def pick_row(df_, c_, r_, g_):
    # tolerate either 'reduction' or 'réduction'
    red_col = "réduction" if "réduction" in df_.columns else "reduction"
    exact = (df_["croissance"] == c_) & (df_[red_col] == r_) & (df_["gain"] == g_)
    if exact.any():
        return df_.loc[exact].iloc[0], True
    idx = ((df_["croissance"] - c_)**2 + (df_[red_col] - r_)**2 + (df_["gain"] - g_)**2).idxmin()
    return df_.loc[idx], False

row, exact_match = pick_row(df, c, r, g)

model_series = row[year_cols].astype(float).values
model_df = pd.DataFrame({"year": years_int, "value": model_series, "series": "Modèle"})

OMI_KNOWN = {
    2025:1.0, 2026:0.988235, 2027:0.976471, 2028:0.964706, 2029:0.952941, 2030:0.941176,
    2031:0.882353, 2032:0.823529, 2033:0.764706, 2034:0.705882, 2035:0.647059, 2036:0.588235,
    2037:0.529412, 2038:0.470588, 2039:0.411765, 2040:0.352941, 2041:0.317647, 2042:0.282353,
    2043:0.247059, 2044:0.211765, 2045:0.176471, 2046:0.141176, 2047:0.105882, 2048:0.070588,
    2049:0.035294, 2050:0.0
}
omi_df = pd.DataFrame({
    "year": years_int,
    "value": [OMI_KNOWN.get(y, 0.0) for y in years_int],
    "series": "Objectif OMI"
})

plot_df = pd.concat([model_df, omi_df], ignore_index=True)

# ---------- Chart ----------
omi_points = plot_df[(plot_df["series"] == "Objectif OMI") & (plot_df["year"].isin([2030, 2040]))]

series_color = alt.Color(
    "series:N",
    title="Séries",
    scale=alt.Scale(domain=["Modèle", "Objectif OMI"], range=["#1f77b4", "#d62728"])
)

chart_lines = (
    alt.Chart(plot_df)
    .mark_line()
    .encode(
        x=alt.X("year:O", title="Années", axis=alt.Axis(format="d")),
        y=alt.Y(
            "value:Q",
            title="Émissions absolues WTW (%)",
            axis=alt.Axis(format="%", grid=True, values=[0, 0.25, 0.5, 0.75, 1.0, 1.25]),
            scale=alt.Scale(domain=[0, 1.25])
        ),
        color=series_color,
        tooltip=["series", "year", alt.Tooltip("value:Q", format=".1%")],
    )
)

chart_points = (
    alt.Chart(omi_points)
    .mark_point(filled=True, size=80, shape="circle")
    .encode(x="year:O", y="value:Q", color=series_color)
)

final_chart = (chart_lines + chart_points).properties(height=520)

with right:
    st.altair_chart(final_chart, use_container_width=True)
    match_text = "✅ Ligne exacte" if exact_match else "ℹ️ Ligne la plus proche utilisée"
    st.caption(f"{match_text} pour (croissance={fmt_pct(c)}, réduction={fmt_pct(r)}, gain={fmt_pct(g)}).")
