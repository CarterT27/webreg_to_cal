# webreg_to_cal
Transforms a webreg schedule into calendar events.

## How to Use
1. Go to (https://act.ucsd.edu/webreg2/start)[https://act.ucsd.edu/webreg2/start]
2. Select the term you want to create the calendar for.
3. Right click the page and click "Save Page As..."
4. Run the following command:
```
python webreg_to_cal.py {filename}
```
Replace {filename} with the path to your saved file.
5. Import the resulting .csv file into your preferred calendar app
    - Example: (https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop)[https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform=Desktop]

## Limitations
- Does not count for breaks and holidays in the middle of quarters.
