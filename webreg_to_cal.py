#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from selectolax.parser import HTMLParser
import datetime
import requests
import sys
import re
import json
import random


class Course:
    def __init__(self, tds: list):
        self.name = tds[0].text().strip()
        self.name = re.sub(r"\s+", " ", self.name)
        self.title = tds[1].text().strip()
        self.section_code = tds[2].text().strip()
        self.meeting_type = tds[3].text().strip()
        self.instructor = tds[4].text().strip()
        self.grade_option = tds[5].text().strip()
        self.units = tds[6].text().strip()
        self.days = tds[7].text().strip()
        self.time = tds[8].text().strip()
        self.parse_time()
        self.bldg = tds[9].text().strip()
        self.room = tds[10].text().strip()
        self.room = "" if self.room == "TBD" else self.room

    def __str__(self):
        if self.meeting_type == "LE":
            return f"{self.name}: {self.title} (LE {self.section_code})"
        elif self.meeting_type == "DI":
            return f"{self.name}: {self.title} (DI {self.section_code})"
        elif self.meeting_type == "LA":
            return f"{self.name}: {self.title} (LA {self.section_code})"
        elif self.meeting_type == "MI":
            return f"{self.name}: {self.title} (MI)"
        elif self.meeting_type == "FI":
            return f"{self.name}: {self.title} (FI)"

    def as_dict(self):
        return {
            "name": self.name,
            "title": self.title,
            "section_code": self.section_code,
            "meeting_type": self.meeting_type,
            "instructor": self.instructor,
            "grade_option": self.grade_option,
            "units": self.units,
            "days": self.days,
            "time": self.time,
            "bldg": self.bldg,
            "room": self.room,
        }

    def parse_time(self):
        times = self.time.split("-")
        self.start_time = times[0].replace("a", " AM").replace("p", " PM")
        self.end_time = times[1].replace("a", " AM").replace("p", " PM")

    def as_df(self, date):
        return pd.DataFrame(
            {
                "Subject": f"{self.name} {self.meeting_type}",
                "Start Date": date,
                "Start Time": self.start_time,
                "End Time": self.end_time,
                "Description": f"{self.title}\nInstructor: {self.instructor}\nTaking as {self.grade_option} for {self.units} units.\n\n---\n\n{random_message(self.meeting_type)}",
                "Location": f"{self.bldg} {self.room}",
            },
            index=[0],
        )


class Break:
    def __init__(self, name, dates):
        self.name = name
        self.dates = dates


def get_webreg_tree(file):
    text = file.read()
    tree = HTMLParser(text)
    return tree


def get_courses(webreg_tree):
    table = webreg_tree.css_first(".ui-jqgrid-view")
    courses = []
    rows = table.css(".ui-row-ltr")
    for i, row in enumerate(rows):
        tds = row.css("td")
        course = Course(tds)
        if course.name == "":
            course.name = courses[-1].name
            course.title = courses[-1].title
            course.instructor = courses[-1].instructor
            course.grade_option = courses[-1].grade_option
            course.units = courses[-1].units
        courses.append(course)
    return courses


def get_academic_year(quarter):
    if "Fall" in quarter:
        return int(quarter.split()[1])
    return int(quarter.split()[1]) - 1


def format_date(date_str, year):
    date_str = ",".join(date_str.split(",")[:2])
    # The date string is expected to be in the format "Day, Month Date"
    # The year is not included in the date string, so it's passed separately
    formatted_date = datetime.datetime.strptime(f"{date_str} {year}", "%A, %B %d %Y")
    return formatted_date.strftime("%m/%d/%Y")


def format_dates(date_str, year):
    date_str = ",".join(date_str.split(",")[:2])
    # Splitting the string into two parts
    start_end_str, month_dates_str = date_str.split(", ")
    month, dates_str = month_dates_str.split(" ")

    # Splitting the dates
    start_date_str, end_date_str = dates_str.split("-")

    # Adding year and formatting
    start_formatted_date = datetime.datetime.strptime(
        f"{month} {start_date_str} {year}", "%B %d %Y"
    ).strftime("%m/%d/%Y")
    end_formatted_date = datetime.datetime.strptime(
        f"{month} {end_date_str} {year}", "%B %d %Y"
    ).strftime("%m/%d/%Y")

    return start_formatted_date, end_formatted_date


def format_date_or_dates(date_str, year):
    date_str = date_str.replace("–", "-")
    if "-" in date_str:
        return format_dates(date_str, year)
    return format_date(date_str, year)


def date_range(start_date, end_date):
    start = datetime.datetime.strptime(start_date, "%m/%d/%Y")
    end = datetime.datetime.strptime(end_date, "%m/%d/%Y")

    delta = end - start
    return [
        (start + datetime.timedelta(days=i)).strftime("%m/%d/%Y")
        for i in range(delta.days + 1)
    ]


def get_term_dates(webreg_tree):
    quarters = webreg_tree.css("#mainpage-select-term > option")
    quarter = None
    for quarter in quarters:
        if 'selected="selected"' in quarter.html:
            break
    quarter_text = quarter.text().replace(" Quarter", "")

    academic_year = get_academic_year(quarter_text)
    calendar_year = int(quarter_text.split()[1])
    url = f"https://blink.ucsd.edu/instructors/resources/academic/calendars/{academic_year}.html"
    response = requests.get(url)

    html = response.text
    parser = HTMLParser(html)

    term_table = parser.css_first("tbody")

    trs = term_table.css("tr")
    quarter_start_date = None
    quarter_end_date = None
    quarter_breaks = []
    # commencement_programs = []
    current_quarter = False
    for tr in trs:
        th = tr.css_first("th")
        if th:
            current_quarter = True if quarter_text in th.text() else False
        elif current_quarter:
            tds = tr.css("td")
            if "Instruction begins" in tds[0].text():
                quarter_start_date = format_date(tds[1].text().strip(), calendar_year)
            elif "Instruction ends" in tds[0].text():
                quarter_end_date = format_date(tds[1].text().strip(), calendar_year)
            elif "Quarter" in tds[0].text():
                pass
            elif "day of instruction" in tds[0].text():
                pass
            elif "Final Exams" in tds[0].text():
                pass
            elif "Commencement programs" in tds[0].text():
                pass
            else:  # holiday
                try:
                    break_s = format_date_or_dates(tds[1].text().strip(), calendar_year)
                    if len(break_s) == 2:
                        for date in date_range(break_s[0], break_s[1]):
                            quarter_breaks.append(date)
                    else:
                        quarter_breaks.append(break_s)
                except:
                    pass

    # Fix so breaks are created as their own events and classes are not scheduled during them
    # summer_session_table = parser.css("tbody")[1] # not implemented
    return quarter_start_date, quarter_end_date


def parse_days(days_str):
    days = []
    i = 0
    while i < len(days_str):
        if i + 1 < len(days_str) and days_str[i : i + 2] in ["Th", "Tu"]:
            days.append(days_str[i : i + 2])
            i += 2
        else:
            days.append(days_str[i])
            i += 1
    return days


def get_course_dates(term_start_date, term_end_date, days_of_week):
    if len(days_of_week.split()) > 1:
        return [days_of_week.split()[1]]
    weekdays = {"M": 0, "Tu": 1, "W": 2, "Th": 3, "F": 4, "Sa": 5, "Su": 6}
    days = [weekdays[day] for day in parse_days(days_of_week) if day in weekdays]

    start_date = datetime.datetime.strptime(term_start_date, "%m/%d/%Y")
    end_date = datetime.datetime.strptime(term_end_date, "%m/%d/%Y")

    course_dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in days:
            course_dates.append(current_date.strftime("%m/%d/%Y"))
        current_date += datetime.timedelta(days=1)

    return course_dates


def random_message(course_type):
    with open("messages.json", "r") as f:
        messages = json.load(f)
    return random.choice(messages[course_type])


def build_cal_df(courses, term_start_date, term_end_date):
    cal_df = pd.DataFrame(
        columns=[
            "Subject",
            "Start Date",
            "Start Time",
            "End Time",
            "Description",
            "Location",
        ]
    )
    for course in courses:
        if course.meeting_type == "LE":
            for date in get_course_dates(term_start_date, term_end_date, course.days):
                cal_df = pd.concat(
                    [
                        cal_df,
                        course.as_df(date),
                    ]
                )
        elif course.meeting_type == "DI":
            for date in get_course_dates(term_start_date, term_end_date, course.days):
                cal_df = pd.concat(
                    [
                        cal_df,
                        course.as_df(date),
                    ]
                )
        elif course.meeting_type == "LA":
            for date in get_course_dates(term_start_date, term_end_date, course.days):
                cal_df = pd.concat(
                    [
                        cal_df,
                        course.as_df(date),
                    ]
                )
        elif course.meeting_type == "MI":
            cal_df = pd.concat(
                [
                    cal_df,
                    course.as_df(
                        get_course_dates(term_start_date, term_end_date, course.days)[0]
                    ),
                ]
            )
        elif course.meeting_type == "FI":
            cal_df = pd.concat(
                [
                    cal_df,
                    course.as_df(
                        get_course_dates(term_start_date, term_end_date, course.days)[0]
                    ),
                ]
            )
    return cal_df.reset_index(drop=True)


# Function to determine the week number from a date string
def get_week_number(date_str):
    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.isocalendar()[1]


def clean_cal_df(df):
    # gets rid of discussions that come before lectures in the week

    # Adding a column for week number
    df["Week Number"] = df["Start Date"].apply(get_week_number)

    # Assuming that lectures and discussions can be identified from the 'Subject' field
    # For example, lecture might be denoted by 'LE' and discussion by 'DI' in the 'Subject' field
    # This assumption needs to be adjusted based on the actual data

    # Identify rows with lectures and discussions
    df["Is Lecture"] = df["Subject"].str.contains("LE")
    df["Is Discussion"] = df["Subject"].str.contains("DI")

    # Group by week number and filter out invalid rows
    valid_rows = []

    for week, group in df.groupby("Week Number"):
        # Check if any discussion is before a lecture in the same week
        lectures_in_week = group[group["Is Lecture"]]
        discussions_in_week = group[group["Is Discussion"]]

        if not discussions_in_week.empty and not lectures_in_week.empty:
            first_lecture_date = min(lectures_in_week["Start Date"])
            invalid_discussions = discussions_in_week[
                discussions_in_week["Start Date"] < first_lecture_date
            ]
            valid_rows.extend(
                group[~group.index.isin(invalid_discussions.index)].index.tolist()
            )
        else:
            # Include all rows if there are no discussions or no lectures in the week
            valid_rows.extend(group.index.tolist())

    # Create a new dataframe with valid rows only
    return df.loc[valid_rows].drop(
        columns=["Week Number", "Is Lecture", "Is Discussion"]
    )


def main(filepath):
    with open(filepath, "r") as f:
        webreg_tree = get_webreg_tree(f)
    courses = get_courses(webreg_tree)
    try:
        term_start_date, term_end_date = get_term_dates(webreg_tree)
    except:
        term_start_date = input(
            "Error: Term Start Date Could not be Found. Please enter in the form %d/%m/%Y"
        )
        term_end_date = input(
            "Error: Term End Date Could not be Found. Please enter in the form %d/%m/%Y"
        )
    cal_df = build_cal_df(courses, term_start_date, term_end_date)
    cal_df.to_csv("WI24.csv", index=False)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        main("WI24.html")
    else:
        print("No command line argument provided")
