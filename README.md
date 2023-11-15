# webreg_to_cal
Transforms a webreg schedule into calendar events.

## Web App
https://webreg.streamlit.app

<details>
<summary>How to Use Locally</summary>
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
4. Run the following command:
```
python -m streamlit run streamlit_app.py
```
</details>

## Limitations
- Does not count for breaks and holidays in the middle of quarters.
