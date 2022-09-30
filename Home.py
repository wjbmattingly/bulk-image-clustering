import streamlit as st
import utils

st.title("USHMM K-Drive Application")

st.sidebar.markdown("# Parameters")
DIRECTORY = st.sidebar.text_area("Directory of files.")
APP_NAME = st.sidebar.text_input("App Name", "default")
NEW_DIRECTORY = st.sidebar.text_area("Directory within the Static Folder of the Application")
NEW_DIRECTORY = f"./{APP_NAME}/static/{NEW_DIRECTORY}"

save_csv = st.sidebar.checkbox("Save CSV")
if save_csv:
    csv_filename = st.sidebar.text_input("CSV Filename")
save_files = st.sidebar.checkbox("Save Image Files")


if st.sidebar.button("Run Processing"):
    utils.process_images(DIRECTORY, APP_NAME, NEW_DIRECTORY,
                   # save_csv=True,
                   # csv_filename="results.csv"
                   # save_files=True
                  )