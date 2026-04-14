
import streamlit as st
import time

def boot_animation():

    placeholder = st.empty()

    steps = [
        "Booting Moto-Renow OS...",
        "Loading AI modules...",
        "Connecting Supabase...",
        "Reading Motor Database...",
        "System Ready ✅"
    ]

    for s in steps:
        placeholder.markdown(f"### {s}")
        time.sleep(0.6)

    placeholder.empty()
