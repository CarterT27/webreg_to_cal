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
import tabula
import numpy as np
import random
import os


class Course:
    def __init__(self, ser):
        self.name = ser["Subject"].strip()
        self.name = re.sub(r"\s+", " ", self.name)
        self.title = ser["Title"].strip()
        self.section_code = "N/A" if ser["Section"] is np.nan else ser["Section"].strip()
        self.meeting_type = ser["Type"].strip()
        self.instructor = ser["Instructor"].strip()
        self.grade_option = ser["Grade"].strip()
        self.units = ser["Units"].strip()
        self.days = ser["Days"].strip()
        self.time = ser["Time"].strip()
        self.parse_time()
        self.bldg = ser["BLDG"].strip()
        self.room = ser["Room"].strip()
        self.room = "" if self.room == "TBD" else self.room
        self.status = ser["Status"].strip()

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
        try:
            self.start_time = times[0].replace("a", " AM").replace("p", " PM")
            self.end_time = times[1].replace("a", " AM").replace("p", " PM")
        except:
            pass

    def as_df(self, date):
        return pd.DataFrame(
            {
                "Subject": f"{self.name} {self.meeting_type}",
                "Start Date": date,
                "Start Time": self.start_time,
                "All Day Event": False,
                "End Time": self.end_time,
                "Description": f"{self.title}\nInstructor: {self.instructor}\nTaking as {self.grade_option} for {self.units} units.\n\n---\n\n{random_message(self.meeting_type)}",
                "Location": f"{self.bldg} {self.room}",
            },
            index=[0],
        )


class AllDayEvent:
    def __init__(self, name, dates):
        self.name = name
        self.dates = dates

    def as_df(self, date):
        return pd.DataFrame(
            {
                "Subject": self.name,
                "Start Date": date or self.dates,
                "All Day Event": True,
                "Start Time": None,
                "End Time": None,
                "Description": None,
                "Location": None,
            },
            index=[0],
        )


class Break(AllDayEvent):
    def __init__(self, name, dates):
        super().__init__(name, dates)

    def as_df(self, date):
        return pd.DataFrame(
            {
                "Subject": self.name,
                "Start Date": date,
                "All Day Event": True,
                "Start Time": None,
                "End Time": None,
                "Description": None,
                "Location": None,
            },
            index=[0],
        )


def get_courses_from_pdf(file):
    def fix_first_letter(string):
        try:
            index = alltext.index(string) - 1
            return alltext[index] + string
        except Exception:
            return string

    filename = f"temp_{random.randint(0, 100)}.pdf"
    with open(filename, "wb") as f:
        f.write(file.getvalue())
    df = tabula.read_pdf(filename, pages=1)[0]

    alltext = df.columns[0]
    df = df.iloc[:-2,:-2]
    headers = df.iloc[0].values
    df.columns = headers
    df.drop(index=0, axis=0, inplace=True)
    df = df.assign(Title = df["Title"].apply(fix_first_letter), Instructor = df["Instructor"].apply(fix_first_letter))
    df = df.rename(columns={"Subject\rCourse": "Subject", "Section\rCode": "Section", "Grade\rOption": "Grade", "Status /\r(Position)": "Status"})
    df.reset_index(drop=True, inplace=True)

    for i, row in df.iterrows():
        if row["Subject"] is np.nan:
            df.iloc[i]["Subject"] = df.iloc[i-1]["Subject"]
            df.iloc[i]["Title"] = df.iloc[i-1]["Title"]
            df.iloc[i]["Instructor"] = df.iloc[i-1]["Instructor"]
            df.iloc[i]["Grade"] = df.iloc[i-1]["Grade"]
            df.iloc[i]["Units"] = df.iloc[i-1]["Units"]
        if row["Status"] is np.nan:
            df.iloc[i]["Status"] = df.iloc[i-1]["Status"]

    # Get courses
    courses = []
    for i, row in df.iterrows():
        if row["Type"] is np.nan:
            continue
        courses.append(Course(row))

    os.remove(filename)

    return courses, alltext


def get_courses_from_file(file):
    return get_courses_from_pdf(file)


def get_academic_year(quarter):
    if "Fall" in quarter:
        return int(quarter.split()[1])
    return int(quarter.split()[1]) - 1


def format_date(date_str, year):
    date_str = ",".join(date_str.split(",")[:2])
    formatted_date = datetime.datetime.strptime(f"{date_str} {year}", "%A, %B %d %Y")
    return formatted_date.strftime("%m/%d/%Y")


def format_dates(date_str, year):
    date_str = ",".join(date_str.split(",")[:2])
    _, month_dates_str = date_str.split(", ")
    month, dates_str = month_dates_str.split(" ")

    start_date_str, end_date_str = dates_str.split("-")

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


def date_range(start_date, end_date=None):
    start = datetime.datetime.strptime(start_date, "%m/%d/%Y")
    if end_date:
        end = datetime.datetime.strptime(end_date, "%m/%d/%Y")

        delta = end - start
        return [
            (start + datetime.timedelta(days=i)).strftime("%m/%d/%Y")
            for i in range(delta.days + 1)
        ]
    return start_date


def get_term_dates(alltext):
    match = re.search(r'\b\w+\b Quarter \b\d{4}\b', alltext)
    quarter = match.group(0) if match else "Fall 2023"
    quarter_text = quarter.replace(" Quarter", "")

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
    commencement_programs = None
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
            elif "Quarter" in tds[0].text():  # ignore table row
                pass
            elif "day of instruction" in tds[0].text():  # ignore table row
                pass
            elif "Final Exams" in tds[0].text():  # ignore?
                pass
            elif "Commencement programs" in tds[0].text():
                commencement_programs = AllDayEvent(
                    "Commencement Programs",
                    format_date_or_dates(tds[1].text().strip(), calendar_year),
                )
            else:  # holiday
                try:
                    break_s_dates = format_date_or_dates(
                        tds[1].text().strip(), calendar_year
                    )
                    break_event = Break(tds[0].text().strip(), break_s_dates)
                    quarter_breaks.append(break_event)
                except Exception as e:
                    print(e)
                    pass

    # summer_session_table = parser.css("tbody")[1] # not implemented
    return quarter_start_date, quarter_end_date, quarter_breaks, commencement_programs


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


def build_cal_df(courses, term_start_date, term_end_date, included_statuses):
    cal_df = pd.DataFrame(
        columns=[
            "Subject",
            "Start Date",
            "Start Time",
            "All Day Event",
            "End Time",
            "Description",
            "Location",
        ]
    )
    for course in courses:
        if course.status not in included_statuses:
            continue
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


def add_breaks_and_commencement(df, break_events, commencement_programs):
    # Add breaks to calendar
    for break_event in break_events:
        if len(break_event.dates) == 2:
            dates = date_range(break_event.dates[0], break_event.dates[1])
        else:
            dates = [break_event.dates]
        for date in dates:
            # Remove lectures, discussions, labs on the same day as breaks
            df = df[df["Start Date"] != date]
            # Add breaks to cal df
            df = pd.concat([df, break_event.as_df(date)])
    # Add commencement programs to calendar
    if commencement_programs:
        df = pd.concat([df, commencement_programs.as_df()])
    return df.reset_index(drop=True)


def get_week_number(date_str):
    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
    return date_obj.isocalendar()[1]


def clean_cal_df(df):
    # gets rid of discussions that come before lectures in the week

    df["Week Number"] = df["Start Date"].apply(get_week_number)

    df["Is Lecture"] = df["Subject"].str.contains("LE")
    df["Is Discussion"] = df["Subject"].str.contains("DI")

    valid_rows = []

    for _, group in df.groupby("Week Number"):
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
            valid_rows.extend(group.index.tolist())

    return df.loc[valid_rows].drop(
        columns=["Week Number", "Is Lecture", "Is Discussion"]
    )


def main(file, *args, **kwargs):
    included_statuses = kwargs.get("included_statuses", None)
    courses, alltext = get_courses_from_file(file)
    (
        term_start_date,
        term_end_date,
        break_events,
        commencement_programs,
    ) = get_term_dates(alltext)
    cal_df = build_cal_df(
        courses, term_start_date, term_end_date, included_statuses
    )
    cal_df = add_breaks_and_commencement(
        cal_df, break_events, commencement_programs
    )
    cal_df = clean_cal_df(cal_df)

    return cal_df.to_csv(index=False).encode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        with open(first_arg, "r") as file:
            main(file)
    else:
        print("No command line argument provided")
