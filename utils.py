def apply_custom_theme(theme: str):
    if theme == "Dark":
        st.markdown(
            """
            <style>
            body {
                background-color: #0e1117;
                color: #ffffff;
            }
            .stApp {
                background-color: #0e1117;
                color: #ffffff;
            }
            .block-container {
                background-color: #0e1117;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    elif theme == "Light":
        st.markdown(
            """
            <style>
            body {
                background-color: #ffffff;
                color: #000000;
            }
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            .block-container {
                background-color: #ffffff;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
