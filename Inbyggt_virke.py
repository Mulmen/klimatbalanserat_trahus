
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title('Dynamisk kolbalans för långlivat virke')

# Parametrar styrda av användaren
rotations_period = st.slider('Skogens rotationsperiod (år)', 50, 150, 80, step=5)
produkt_livslangd = st.slider('Produktens livslängd (år)', 10, 100, 50, step=5)
kolinlagring_per_ar = st.slider('Kolinlagring per år i skogen (ton)', 0.1, 5.0, 1.5, step=0.1)
andel_kol_i_virke = st.slider('Andel kol i virket', 0.3, 0.6, 0.5, step=0.05)
tidsperiod = st.slider('Total analysperiod (år)', 50, 200, 150, step=10)

# Dynamisk kolbalansmodell
def kolbalans(rotations_period, produkt_livslangd, kolinlagring_per_ar, andel_kol_i_virke, tidsperiod):
    ar = np.arange(tidsperiod)
    kol_i_skog = np.zeros(tidsperiod)
    kol_i_produkt = np.zeros(tidsperiod)

    for i in ar:
        cykel_ar = i % rotations_period
        kol_i_skog[i] = cykel_ar * kolinlagring_per_ar

    for i in ar:
        if i % rotations_period == 0 and i != 0:
            kol_uttaget = rotations_period * kolinlagring_per_ar * andel_kol_i_virke
            slut_ar = min(i + produkt_livslangd, tidsperiod)
            kol_i_produkt[i:slut_ar] += kol_uttaget / produkt_livslangd

    netto_kolbalans = kol_i_skog + kol_i_produkt
    return ar, kol_i_skog, kol_i_produkt, netto_kolbalans

ar, kol_i_skog, kol_i_produkt, netto_kolbalans = kolbalans(
    rotations_period, produkt_livslangd, kolinlagring_per_ar, andel_kol_i_virke, tidsperiod)

# Skapa grafen
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(ar, kol_i_skog, label='Kol i skog (ton)')
ax.plot(ar, kol_i_produkt, label='Kol i produkt (ton)')
ax.plot(ar, netto_kolbalans, label='Netto kolbalans (ton)', linestyle='--', linewidth=2)
ax.axvline(x=produkt_livslangd, color='red', linestyle=':', label='Slut på produktlivslängd')
ax.set_xlabel('År')
ax.set_ylabel('Kol (ton)')
ax.set_title('Dynamisk kolbalans över tid')
ax.legend()
ax.grid(True)

st.pyplot(fig)
