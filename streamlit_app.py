import streamlit as st
import webreg_to_cal


def main():
    if "show_instructions" not in st.session_state:
        st.session_state["show_instructions"] = False

    st.title("Webreg to Cal")
    "Export your webreg schedule to your favorite calendar app in seconds!"

    if st.button("How to Use"):
        st.session_state["show_instructions"] = not st.session_state[
            "show_instructions"
        ]

    if st.session_state["show_instructions"]:
        st.write(
            "1. Visit https://act.ucsd.edu/webreg2/start and once you are logged in, select the term that you want to add to your calendar."
        )
        st.write(
            '2. Once you are at the schedule page, click "Print Schedule" and save the .pdf file.'
        )
        st.write(
            "3. Upload the .pdf file that you just saved back to this website, and it will automatically generate calendar events that you can import to your [Google Calendar](https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop) (or another calendar app that supports .csv file imports)."
        )

    included_statuses = st.multiselect(
        "Choose Course Statuses to Transfer:",
        [
            "Planned",
            "Enrolled",
            "Waitlisted",
        ],
    )

    uploaded_file = st.file_uploader(
        "Upload your webreg schedule in .pdf format", type="pdf"
    )
    if uploaded_file is not None:
        if included_statuses == []:
            st.error("Warning: No course statuses selected. Only quarter breaks will be added to your calendar.")
        # try:
        with st.spinner("Processing..."):
            cal_csv = webreg_to_cal.main(uploaded_file, included_statuses=included_statuses)

        st.success(
            "Successfully converted schedule to .csv. Click below to download file."
        )

        st.download_button(
            label="Download Webreg CSV",
            data=cal_csv,
            file_name="Webreg_Schedule.csv",
            mime="text/csv",
        )
        # except Exception as e:
        #     # raise (e)
        #     print(e)
        #     st.error(
        #         "Error: Could not process file. Please ensure you are uploading the correct file type. "
        #         "For more information, please consult the How to Use section."
        #     )

    st.write("Questions/Suggestions: https://github.com/CarterT27/webreg_to_cal/issues")
    "Made by Carter Tran"


if __name__ == "__main__":
    main()
