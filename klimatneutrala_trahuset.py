import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Policyjusterad klimatneutralitet", layout="wide")

st.title("🌲 Policyjusterad klimatneutralitet för trähus")
st.markdown(
    "Hur klimatbalanserad kan ett trähus bli över tid – med hänsyn till både skogsproduktion och policy?"
)

st.sidebar.header("Justerbara modellparametrar")

BTA = st.sidebar.slider("Bostadsyta (BTA), m²", 100, 10000, 150)
virke_per_m2 = st.sidebar.slider("Mängd stomvirke (m³/m² BTA)", 0.1, 1.0, 0.35)
bonitet = st.sidebar.slider("Bonitet (m³ virke/ha/år)", 4.0, 10.0, 8.0, 0.1)
LCA_period = st.sidebar.slider("LCA-period (år, analys)", 30, 100, 50)
rotation = st.sidebar.slider("Skogens rotationsperiod (år)", 50, 150, 80)
hus_livslangd = st.sidebar.slider("Husets livslängd (år)", 20, 200, 100)
max_years = st.sidebar.slider("Total tidsperiod (år)", 50, 200, 200)

klimatpåverkan_per_m2 = st.sidebar.slider(
    "Husets klimatpåverkan (ton CO₂/m² BTA)", 0.150, 0.500, 0.250
)

alternativ = {
    "Återanvänds till nytt hus": "ateranvandning",
    "Energiåtervinns med bio-CCS (koldioxidlagring)": "bioccs",
    "Bränns konventionellt (släpper ut all CO₂)": "konventionell"
}
valt_svar = st.sidebar.selectbox(
    "Vad händer med virket efter husets rivning?",
    options=list(alternativ.keys()),
    index=0
)
virkes_hantering = alternativ[valt_svar]
bygg_igen = st.sidebar.checkbox("Bygg nytt hus efter livslängd?", value=True)

years = np.arange(max_years+1)

kg_torrsubstans_per_m3 = 750
kolandel = 0.5
co2_per_kg_kol = 3.67

virkesvolym_total = BTA * virke_per_m2
kol_total = virkesvolym_total * kg_torrsubstans_per_m3 * kolandel
co2_total = kol_total * co2_per_kg_kol / 1000
co2_per_m3 = kg_torrsubstans_per_m3 * kolandel * co2_per_kg_kol / 1000

virke_per_ha_per_rotation = bonitet * rotation
skogsareal_ha = virkesvolym_total / virke_per_ha_per_rotation
klimatpåverkan_total = BTA * klimatpåverkan_per_m2

# --- Policy-faktor ---
policyfaktor = min(1, LCA_period / rotation)  # Ex: 50/100 år = 0.5
max_klimatbalansering = np.full_like(years, policyfaktor * 100)

# --- Simulering av skog och hus ---
co2_i_skog = np.zeros_like(years, dtype=float)
co2_i_hus = np.zeros_like(years, dtype=float)

for t in years:
    tid_i_rotation = t % rotation
    co2_i_skog[t] = skogsareal_ha * bonitet * co2_per_m3 * tid_i_rotation

    if bygg_igen:
        antal_hus = t // hus_livslangd + 1
    else:
        antal_hus = 1 if t < hus_livslangd else 0

    if virkes_hantering == "konventionell":
        if bygg_igen:
            tid_i_hus = t % hus_livslangd
            if tid_i_hus < hus_livslangd:
                co2_i_hus[t] = co2_total
            else:
                co2_i_hus[t] = 0
        else:
            if t < hus_livslangd:
                co2_i_hus[t] = co2_total
            else:
                co2_i_hus[t] = 0

    elif virkes_hantering in ("ateranvandning", "bioccs"):
        if bygg_igen:
            co2_i_hus[t] = antal_hus * co2_total  # Trappa
        else:
            if t < hus_livslangd:
                co2_i_hus[t] = co2_total  # Block
            else:
                co2_i_hus[t] = co2_total  # Block fortsätter

    else:
        co2_i_hus[t] = 0

# --- Klimatneutralitetsgrad (utan policy) ---
klimatneutralitet = np.zeros_like(years, dtype=float)
for t in years:
    if klimatpåverkan_total > 0:
        klimatneutralitet[t] = 100 * co2_i_skog[t] / klimatpåverkan_total
    else:
        klimatneutralitet[t] = np.nan

# --- Policyjusterad klimatneutralitet ---
klimatneutralitet_policy = klimatneutralitet * policyfaktor

st.info(
    f"**Total skogsareal som krävs för att producera virket till huset är:**\n"
    f"**{skogsareal_ha:.4f} ha** (givet vald bonitet och rotationsperiod)."
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(years, klimatneutralitet_policy, lw=3, color="orange", label="Policyjusterad klimatneutralitet (%)")
ax.plot(years, klimatneutralitet, lw=1.5, color="blue", alpha=0.6, linestyle="--", label="Teoretisk klimatneutralitet (%)")
ax.axhline(100, color='gray', linestyle='--', label="100% klimatbalans")
ax.axvline(LCA_period, color='red', linestyle=':', label='LCA-period slutar')
ax.axvline(rotation, color='green', linestyle='--', label='En rotationsperiod')
ax.set_xlabel("Tid (år)")
ax.set_ylabel("Klimatneutralitetsgrad (%)")
ax.set_ylim(0, 150)
ax.set_title("Policyjusterad klimatneutralitet över tid")
ax.legend()
ax.grid(alpha=0.3)

st.subheader("Policyjusterad klimatneutralitet över tid")
st.pyplot(fig)
st.markdown(
    f"""Den orange kurvan visar **klimatneutralitetsgraden** multiplicerat med policy-faktorn (LCA-period/rotationsperiod).  
    Den blå streckade kurvan visar klimatneutraliteten om man ignorerar policybegränsning.
    """,
    unsafe_allow_html=True
)

with st.expander("Vetenskaplig bakgrund & källor"):
    st.markdown(
        f"""
        - Bonitet anger årlig volymtillväxt (m³ virke/ha/år).
        - **Skogsarealen beräknas utifrån husets virkesbehov och skogens produktionsförmåga:**
            - Skogsareal = Bostadsyta × mängd stomvirke per m² / (bonitet × rotationstid)
            - För dessa parametrar: **skogsareal ≈ {skogsareal_ha:.4f} ha**
        - Omvandlingsfaktor: 1 m³ virke = 750 kg torrsubstans (50% kol), 1 kg C = 3,67 kg CO₂.
        - Klimatneutralitetsgrad = (ackumulerad CO₂ i skog / husets totala klimatpåverkan) × 100.
        - Policyfaktor = (LCA-period/rotationsperiod), max 1.
        - Vid “Bränns konventionellt” nollställs klimatnyttan varje gång huset rivs.
        - Hantering av virke vid rivning styr fortsatt kolinlagring (se IVL/SLU-rapporter).
        """
    )

st.markdown(
    "<small>Utvecklad av [Johan Holmqvist/IVL]. Kod på "
    "[GitHub repository](https://github.com/Mulmen/klimatbalanserat_trahus).</small>",
    unsafe_allow_html=True
)
