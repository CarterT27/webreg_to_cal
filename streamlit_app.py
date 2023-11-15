import streamlit as st
import webreg_to_cal


def main():
    st.title("Webreg to Cal")
    st.subheader("Made by Carter Tran")

    st.header("How to Use")
    st.write("1. Visit https://act.ucsd.edu/webreg2/start and once you are logged in, select the term that you want to add to your calendar.")
    st.write('2. Once you are at the schedule page, right click the page and click "Save As", "Save Page As...", or something similar.')
    st.write("3. Upload the .html file that you just saved back to this website, and it will automatically generate calendar events that you can import to your Google Calendar (or another calendar app that supports .csv file imports).")

    st.write("Instructions on importing to Google Calendar: https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop")

    st.write("Please let me know if you have any questions/suggestions!")

    uploaded_file = st.file_uploader("Choose an HTML file", type="html")
    if uploaded_file is not None:
        # Show loading message
        with st.spinner("Processing..."):
            # Process the file
            webreg_tree = webreg_to_cal.get_webreg_tree(uploaded_file)
            courses = webreg_to_cal.get_courses(webreg_tree)
            term_start_date, term_end_date = webreg_to_cal.get_term_dates(webreg_tree)
            cal_df = webreg_to_cal.build_cal_df(courses, term_start_date, term_end_date)

        # Convert processed data to CSV for download
        cal_csv = cal_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Calendar CSV",
            data=cal_csv,
            file_name="processed.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
