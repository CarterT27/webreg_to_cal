import streamlit as st
import webreg_to_cal


def main():
    # Initialize the session state
    if "show_instructions" not in st.session_state:
        st.session_state["show_instructions"] = False

    st.title("Webreg to Cal")
    "Export your webreg schedule to your favorite calendar app in less than a minute!"

    # When the button is clicked, toggle the state
    if st.button("How to Use"):
        st.session_state["show_instructions"] = not st.session_state[
            "show_instructions"
        ]

    # Show or hide the instructions based on the state
    if st.session_state["show_instructions"]:
        st.write(
            "1. Visit https://act.ucsd.edu/webreg2/start and once you are logged in, select the term that you want to add to your calendar."
        )
        st.write(
            '2. Once you are at the schedule page, right click the page and click "Save As", "Save Page As...", or something similar.',
            "The default filename should be webregMain.html",
        )
        st.write(
            "3. Upload the .html file that you just saved back to this website, and it will automatically generate calendar events that you can import to your Google Calendar (or another calendar app that supports .csv file imports)."
        )

        st.write(
            "Instructions on importing to Google Calendar: https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop"
        )

        st.write("Please let me know if you have any questions/suggestions!")

    uploaded_file = st.file_uploader(
        "Upload your webreg schedule in .html format", type="html"
    )
    if uploaded_file is not None:
        try:
            # Show loading message
            with st.spinner("Processing..."):
                # Process the file
                webreg_tree = webreg_to_cal.get_webreg_tree(uploaded_file)
                courses = webreg_to_cal.get_courses(webreg_tree)
                term_start_date, term_end_date, break_events, commencement_programs = webreg_to_cal.get_term_dates(
                    webreg_tree
                )
                cal_df = webreg_to_cal.build_cal_df(
                    courses, term_start_date, term_end_date
                )
                cal_df = webreg_to_cal.add_breaks_and_commencement(cal_df, break_events, commencement_programs)
                cal_df = webreg_to_cal.clean_cal_df(cal_df)

            # Convert processed data to CSV for download
            cal_csv = cal_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Calendar CSV",
                data=cal_csv,
                file_name="Webreg_Schedule.csv",
                mime="text/csv",
            )
        except Exception as e:
            raise (e)
            print(e)
            st.write(
                "Error: Could not process file. Please ensure you are uploading the correct file type."
            )
            st.write("For more information, please consult the How to Use section.")

    "Made by Carter Tran"


if __name__ == "__main__":
    main()
