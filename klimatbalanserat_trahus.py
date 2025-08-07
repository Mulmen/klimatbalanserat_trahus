import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Klimatbalanserat trähus. Ver 1.7", layout="wide")
st.title("🌲 Klimatbalanserat trähus – dynamisk modell")
st.markdown("""
Modellera klimatnyttan av att bygga trähus och plantera produktiv skog!
Justera parametrar, analysera CO₂-bindning, och välj vad som sker när huset rivs.
""")

st.sidebar.header("Justera modellparametrar")

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

klimatbalans_maxandel = min(100 * LCA_period / rotation, 100)
procentandel = np.full_like(years, klimatbalans_maxandel)
fig0, ax0 = plt.subplots(figsize=(8, 3))
ax0.plot(years, procentandel, color='darkorange', lw=3, label="Max klimatbalanserbar andel (%)")
ax0.set_xlabel("Tid (år)")
ax0.set_ylabel("Max klimatbalansering (%)")
ax0.set_title("Maximal klimatbalanserbar andel av inbyggd CO₂ enligt policy")
ax0.set_ylim(0, 110)
ax0.grid(alpha=0.3)
ax0.axvline(LCA_period, color='red', linestyle=':', label='LCA-period slutar')
ax0.axvline(rotation, color='green', linestyle='--', label='En rotationsperiod')
ax0.legend(loc="upper right")

# --- Simulering ---
co2_i_skog = np.zeros_like(years, dtype=float)
co2_i_hus = np.zeros_like(years, dtype=float)

for t in years:
    tid_i_rotation = t % rotation
    co2_i_skog[t] = skogsareal_ha * bonitet * co2_per_m3 * tid_i_rotation

    if virkes_hantering in ("ateranvandning", "bioccs"):
        if bygg_igen:
            antal_hus = t // hus_livslangd + 1
            co2_i_hus[t] = antal_hus * co2_total
        else:
            co2_i_hus[t] = co2_total  # Lagring för alltid (eller till analysperiodens slut)
    elif virkes_hantering == "konventionell":
        if bygg_igen:
            tid_i_hus = t % hus_livslangd
            co2_i_hus[t] = co2_total if tid_i_hus < hus_livslangd else 0
        else:
            co2_i_hus[t] = co2_total if t < hus_livslangd else 0
    else:
        co2_i_hus[t] = 0

klimatneutralitet = 100 * co2_i_skog / klimatpåverkan_total
kumulativt_netto = co2_i_skog - co2_i_hus

st.info(f"**Total skogsareal som krävs för att producera virket till huset är:**\n"
        f"**
