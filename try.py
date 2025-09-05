import streamlit as st

user_input = st.text_input("You: ")

if user_input:

    with st.chat_message("user"):
        st.text(user_input)

    
    with st.chat_message("assistant"):
        st.text("Hello!")
        