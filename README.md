# webreg_to_cal
Transforms a webreg schedule into calendar events.

## Web App
https://webreg.streamlit.app

---

## How to Use Locally
1. Clone this repository and cd into it
```
$ git clone https://github.com/CarterT27/webreg_to_cal
$ cd webreg_to_cal
```
2. (Optional) Create and activate a virtual environment for the project
```
$ python -m venv venv
$ source venv/bin/activate
```
3. Install the dependencies
```
$ pip install -r requirements.txt
```
4. Go to https://act.ucsd.edu/webreg2/start
5. Select the term you want to create the calendar for.
6. Right click the page and click "Save Page As..."
7. Save the .html file into the directory of this project (webreg_to_cal)
8. Run the following command:
```
python webreg_to_cal.py {filename}
```
Replace {filename} with the path to your saved file.
9. Import the resulting .csv file into your preferred calendar app
    - Example: https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop

## Limitations
- Does not count for breaks and holidays in the middle of quarters.
