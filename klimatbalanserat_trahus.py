import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Klimatbalanserat trähus", layout="wide")

st.title("🌲 Klimatbalanserat trähus – dynamisk modell")
st.markdown("""
Modellera klimatnyttan av att bygga trähus och plantera produktiv skog!
Justera parametrar, analysera CO₂-bindning, och välj vad som sker när huset rivs.
""")

# --- SIDOPANEL: ANVÄNDARVAL & DEFAULTS ---
st.sidebar.header("Justera modellparametrar")

BTA = st.sidebar.slider("Bostadsyta (BTA), m²", 100, 10000, 150)
virke_per_m2 = st.sidebar.slider("Mängd stomvirke (m³/m² BTA)", 0.1, 1.0, 0.35)
bonitet = st.sidebar.slider("Bonitet gran (T/ha/år)", 4, 10, 8)  # m³sk/ha/år
LCA_period = st.sidebar.slider("LCA-period (år, analys)", 30, 100, 50)
rotation = st.sidebar.slider("Skogens rotationsperiod (år)", 50, 150, 80)
hus_livslangd = st.sidebar.slider("Husets livslängd (år)", 20, 200, 100)
max_years = st.sidebar.slider("Total tidsperiod (år)", 50, 200, 200)

virkes_hantering = st.sidebar.selectbox(
    "Vad händer med virket efter husets rivning?",
    (
        "Återanvänds till nytt hus",
        "Energiåtervinns med bio-CCS (koldioxidlagring)",
        "Bränns konventionellt (släpper ut all CO₂)"
    ),
    index=0
)

years = np.arange(max_years+1)

# --- FAKTA / OMFATTNING ---
kg_torrsubstans_per_m3 = 750
kolandel = 0.5
co2_per_kg_kol = 3.67

virkesvolym_total = BTA * virke_per_m2  # m³ virke
kol_total = virkesvolym_total * kg_torrsubstans_per_m3 * kolandel  # kg kol
co2_total = kol_total * co2_per_kg_kol / 1000  # ton CO2

tillvaxt_skogen_m3_per_ha_ar = bonitet
co2_per_m3 = kg_torrsubstans_per_m3 * kolandel * co2_per_kg_kol / 1000  # ton CO2/m³

skogsareal_ha = co2_total / (tillvaxt_skogen_m3_per_ha_ar * co2_per_m3 * rotation)

# --- SIMULERING: SKOGSROTATIONER & HUSCYKLER ---
co2_i_skog = np.zeros_like(years, dtype=float)
co2_i_hus = np.zeros_like(years, dtype=float)

for t in years:
    # Skogen: ackumulerar CO2 linjärt varje rotation, nollställs vid avverkning, startar om
    tid_i_rotation = t % rotation
    co2_i_skog[t] = skogsareal_ha * tillvaxt_skogen_m3_per_ha_ar * co2_per_m3 * tid_i_rotation

    # Hus: olika logik beroende på hantering efter rivning
    cykel_hus = t // hus_livslangd
    tid_i_hus = t % hus_livslangd

    if virkes_hantering == "Återanvänds till nytt hus":
        co2_i_hus[t] = co2_total
    else:
        # För bio-CCS eller konventionell förbränning:
        # CO2 bara under tiden huset faktiskt finns (dvs under sin livslängd)
        if tid_i_hus < hus_livslangd:
            co2_i_hus[t] = co2_total
        else:
            co2_i_hus[t] = 0

# --- Klimatneutralitet (%) ---
klimatneutralitet = np.zeros_like(years, dtype=float)
for t in years:
    if co2_i_hus[t] > 0:
        klimatneutralitet[t] = 100 * co2_i_skog[t] / co2_i_hus[t]
    else:
        klimatneutralitet[t] = np.nan

# --- Kumulativt netto (CO2 i skog minus CO2 i hus, över tid) ---
kumulativt_netto = co2_i_skog - co2_i_hus

# --- GRAFER ---
fig1, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(years, co2_i_hus, label="Inbyggd CO₂ i trähus (ton)", lw=2)
ax1.plot(years, co2_i_skog, label="Ackumulerad CO₂ i skog (ton)", lw=2)
ax1.axvline(LCA_period, color='red', linestyle=':', label='LCA-period slutar')
for n in range(0, max_years, rotation):
    ax1.axvline(n, color='green', linestyle='--', alpha=0.2)
for n in range(0, max_years, hus_livslangd):
    ax1.axvline(n, color='brown', linestyle=':', alpha=0.2)
ax1.set_xlabel("Tid (år)")
ax1.set_ylabel("Ton CO₂")
ax1.set_title("CO₂-lagring i hus och skog")
ax1.legend()
ax1.grid(alpha=0.3)

fig2, ax2 = plt.subplots(figsize=(8, 4))
ax2.plot(years, klimatneutralitet, label="Klimatneutralitet (%)", lw=2, color="purple")
ax2.axhline(100, color='gray', linestyle='--', label="100% klimatbalans")
ax2.set_xlabel("Tid (år)")
ax2.set_ylabel("Klimatneutralitetsgrad (%)")
ax2.set_ylim(0, 150)
ax2.set_title("Klimatneutralitet över tid")
ax2.legend()
ax2.grid(alpha=0.3)

fig3, ax3 = plt.subplots(figsize=(8, 4))
ax3.plot(years, kumulativt_netto, label="Kumulativt netto (skog - hus) [ton CO₂]", lw=2, color="teal")
ax3.axhline(0, color='gray', linestyle='--', label="Noll-linje")
ax3.set_xlabel("Tid (år)")
ax3.set_ylabel("Ton CO₂")
ax3.set_title("Kumulativt netto: skogsupptag minus lagrat i hus")
ax3.legend()
ax3.grid(alpha=0.3)

# --- UTLAYOUT STREAMLIT ---
st.subheader("CO₂-lagring i trähus och produktiv skog över tid")
st.pyplot(fig1)
st.subheader("Klimatneutralitetsgrad för trähus över tid")
st.pyplot(fig2)
st.subheader("Kumulativt netto – skillnad mellan skogsupptag och inbyggd CO₂ i hus")
st.pyplot(fig3)

with st.expander("Vetenskaplig bakgrund & källor"):
    st.markdown("""
    - Omvandlingsfaktor: 1 m³ virke = 750 kg torrsubstans (50% kol), 1 kg C = 3,67 kg CO₂.
    - Bonitet: Tillväxt i m³/ha/år enligt Skogsstyrelsen och SLU, t.ex. https://www.skogsstyrelsen.se.
    - Ackumulerad CO₂ i skog nollställs vid varje ny skogsrotation, därefter planteras ny skog.
    - Klimatneutralitet = (ackumulerad CO₂ i skog / inbyggd CO₂ i trähus) × 100.
    - Hantering av virke vid rivning styr fortsatt kolinlagring (se IVL/SLU-rapporter).
    """)

st.markdown("""
<small>Utvecklad av [Johan Holmqvist/IVL]. Kod på [GitHub repository](https://github.com/Mulmen/klimatbalanserat_trahus).</small>
""", unsafe_allow_html=True)
