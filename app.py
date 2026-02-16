from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from comtrade import Comtrade

from src.comtrade_analyzer import (
    EventThresholds,
    LineContext,
    build_analysis_report,
    detect_threshold_events,
    estimate_fault_distance_km,
    summarize_signal_metrics,
)

st.set_page_config(page_title="COMTRADE Disturbance Analyzer", layout="wide")
st.title("Leitor COMTRADE + Análise de Desligamento/Perturbações")

st.markdown(
    "Faça upload dos arquivos `.cfg` e `.dat`, informe parâmetros da linha e obtenha uma análise preliminar."
)

cfg_file = st.file_uploader("Arquivo CFG", type=["cfg"])
dat_file = st.file_uploader("Arquivo DAT", type=["dat"])

col1, col2, col3 = st.columns(3)
with col1:
    line_length_km = st.number_input("Comprimento da linha (km)", min_value=0.1, value=100.0)
with col2:
    voltage_class_kv = st.number_input("Classe de tensão (kV)", min_value=1.0, value=230.0)
with col3:
    z1_ohm_km = st.number_input("Impedância positiva (Ohm/km)", min_value=0.001, value=0.4)

st.subheader("Limiar de eventos")
c1, c2, c3 = st.columns(3)
with c1:
    overcurrent_a = st.number_input("Sobrecorrente (A)", min_value=1.0, value=500.0)
with c2:
    overvoltage_pu = st.number_input("Sobretensão (pu)", min_value=0.5, value=1.1)
with c3:
    undervoltage_pu = st.number_input("Subtensão (pu)", min_value=0.0, max_value=1.0, value=0.8)

if cfg_file and dat_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg_path = Path(tmpdir) / cfg_file.name
        dat_path = Path(tmpdir) / dat_file.name
        cfg_path.write_bytes(cfg_file.read())
        dat_path.write_bytes(dat_file.read())

        rec = Comtrade()
        rec.load(str(cfg_path), str(dat_path))

        analog_labels = [lbl.strip() for lbl in rec.analog_channel_ids]
        time = np.array(rec.time, dtype=float)
        analog_data = {label: np.array(values, dtype=float) for label, values in zip(analog_labels, rec.analog)}
        df = pd.DataFrame({"time": time, **analog_data})

        st.success(f"Registro carregado com {len(df)} amostras e {len(analog_labels)} canais analógicos.")

        default_voltage = [c for c in analog_labels if c.upper().startswith("V")]
        default_current = [c for c in analog_labels if c.upper().startswith("I")]

        voltage_cols = st.multiselect(
            "Selecione canais de tensão",
            options=analog_labels,
            default=default_voltage[:3] if default_voltage else analog_labels[:1],
        )
        current_cols = st.multiselect(
            "Selecione canais de corrente",
            options=analog_labels,
            default=default_current[:3] if default_current else analog_labels[:1],
        )

        nominal_voltage_v = max(voltage_class_kv * 1000 / np.sqrt(3), 1.0)

        selected_cols = sorted(set(voltage_cols + current_cols))
        metrics_df = summarize_signal_metrics(df, selected_cols)

        thresholds = EventThresholds(
            overcurrent_a=overcurrent_a,
            overvoltage_pu=overvoltage_pu,
            undervoltage_pu=undervoltage_pu,
        )
        events_df = detect_threshold_events(
            df,
            voltage_cols=voltage_cols,
            current_cols=current_cols,
            nominal_voltage_v=nominal_voltage_v,
            thresholds=thresholds,
        )

        line_ctx = LineContext(
            line_length_km=line_length_km,
            voltage_class_kv=voltage_class_kv,
            positive_seq_impedance_ohm_per_km=z1_ohm_km,
        )

        fault_distance_km = 0.0
        if voltage_cols and current_cols:
            fault_distance_km = estimate_fault_distance_km(
                df[voltage_cols[0]].to_numpy(dtype=float),
                df[current_cols[0]].to_numpy(dtype=float),
                line_ctx,
            )

        st.subheader("Métricas")
        st.dataframe(metrics_df, use_container_width=True)

        st.subheader("Eventos detectados")
        if events_df.empty:
            st.info("Nenhum evento acima dos limiares.")
        else:
            st.dataframe(events_df, use_container_width=True)

        st.metric("Distância estimada da falta", f"{fault_distance_km:.2f} km")

        st.subheader("Formas de onda")
        fig = go.Figure()
        for col in selected_cols:
            fig.add_trace(go.Scatter(x=df["time"], y=df[col], mode="lines", name=col))
        fig.update_layout(height=450, xaxis_title="Tempo (s)", yaxis_title="Amplitude")
        st.plotly_chart(fig, use_container_width=True)

        report = build_analysis_report(metrics_df, events_df, fault_distance_km, line_ctx)
        st.subheader("Resumo textual")
        st.text_area("Relatório", report, height=280)
else:
    st.info("Envie arquivos `.cfg` e `.dat` para iniciar a análise.")
