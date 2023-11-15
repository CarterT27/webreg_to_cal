import streamlit as st
import webreg_to_cal


def main():
    st.title("Webreg to Cal")

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
