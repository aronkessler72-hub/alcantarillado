    st.dataframe(
        df_res.style.applymap(destacar_estado, subset=['Estado']),
        use_container_width=True
    )

    # -----------------------------------------------------------------------------
    # GRÁFICOS INTERACTIVOS (PLOTLY)
    # -----------------------------------------------------------------------------
    st.subheader("📈 Gráficos de Perfil e Hidráulica")
    tab1, tab2 = st.tabs(["Tensión Tractiva & Velocidad", "Relación Tirante h/D"])

    with tab1:
        fig1 = px.bar(
            df_res, x="Tramo", y="Tensión Tractiva (Pa)",
            color="Estado",
            title="Tensión Tractiva por Tramo vs Límite de Autolimpieza (1.0 Pa)",
            color_discrete_map={"CUMPLE NORMA": "#2b8a3e", "REVISAR: Tau bajo": "#c92a2a"}
        )
        fig1.add_hline(y=tau_min, line_dash="dash", line_color="red", annotation_text="Límite Autolimpieza (1.0 Pa)")
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        fig2 = px.line(
            df_res, x="Tramo", y="h/D (%)",
            markers=True,
            title="Relación Tirante / Diámetro (h/D) por Tramo"
        )
        fig2.add_hline(y=h_d_max*100, line_dash="dash", line_color="orange", annotation_text=f"Máximo Permitido ({h_d_max*100}%)")
        st.plotly_chart(fig2, use_container_width=True)

    # Exportar
    st.subheader("📥 Exportar Resultados")
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Descargar Planilla Completa en CSV",
        data=csv,
        file_name="Planilla_Calculo_Hidraulico_Alcantarillado.csv",
        mime="text/csv"
    )
