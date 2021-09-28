# Libraries for scraper
from bs4 import BeautifulSoup, Comment
import numpy as np
import pandas as pd
import urllib.request
import requests
# Libraries for gsheets export
import gspread
# Libraries for running apps script
import pickle
import os.path
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# Libraries for dates
import datetime
import math

## Helper functions

# gets weekday of game give html div
def get_day(wk_day_span):
    wk_day_txt = wk_day_span.text.strip()
    date_components = wk_day_txt.split(' ')
    return(date_components[0])

# gets opposite of home line formatted correctly
def get_away_line(home_line):
    home_line = int(home_line) if float(home_line).is_integer() else float(home_line)
    if home_line < 0:
        return("{0:+}".format(home_line * -1))
    elif home_line > 0:
        return("{0:-}".format(home_line * -1))
    return('0')

## Scraping functions
def get_game_info(score_box):
    odds = score_box.find_all('td', {'class': 'in-progress-odds'})
    over_under = odds[0].text.strip()[1:]
    home_line = odds[1].text.strip()
    away_line = get_away_line(home_line)
    teams = score_box.find_all('td', {'class': 'team'})
    wk_day_span = score_box.find('span', {'class': 'game-status'})
    wk_day = get_day(wk_day_span)
    away_team = teams[0]
    home_team = teams[1]
    away_team_name = away_team.find_all('a')[1].text
    away_team_abbr = away_team.find('a')['href'].split('/')[5]
    home_team_name = home_team.find_all('a')[1].text
    home_team_abbr = home_team.find('a')['href'].split('/')[5]
    game_info_array = [home_team_name, home_team_abbr, away_team_name, away_team_abbr,
                     home_line, away_line, over_under, wk_day]
    return(game_info_array)

def get_game_info_df(week_num):
    link = 'https://www.cbssports.com/nfl/scoreboard/all/2021/regular/' + str(week_num) + '/'
    with urllib.request.urlopen(link) as url:
        page = url.read()
    soup = BeautifulSoup(page, "html.parser")
    # list of game info boxes for all games
    score_boxes = soup.find_all('div', {'class':'live-update'})
    #game_info_list = np.array([])
    game_info_matrix = []
    for score_box in score_boxes:
        #print(score_box)
        game_info_matrix.append(get_game_info(score_box))
    cols = ['home_team_name', 'home_team_abbr', 'away_team_name', 
        'away_team_abbr', 'home_line', 'away_line', 
        'over_under', 'wk_day']
    game_info_df = pd.DataFrame(game_info_matrix, columns=cols)
    game_info_df['wk_num'] = str(week_num)
    return(game_info_df)

## Google sheets functions
def export_to_gsheets(df, week_num):
    # open connection to gsheets
    gc = gspread.oauth()
    sh = gc.open("Pickem Lines Data")
    # create new worksheet for the given week
    worksheet_name = 'week' + str(week_num)
    sh.add_worksheet(worksheet_name, rows=df.shape[0], cols=df.shape[1])
    worksheet = sh.worksheet(worksheet_name)
    # push df to google sheet
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

def run_export_process(week_num):
    df = get_game_info_df(week_num)
    export_to_gsheets(df, week_num)

## Apps script API functions
def get_scripts_service():
    """Calls the Apps Script API.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('.credentials/scripts/token.pickle'):
        with open('.credentials/scripts/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Credentials path from the credentials .json file 
            # from step 3 from Google Cloud Platform section
            flow = InstalledAppFlow.from_client_secrets_file(
                '.credentials/scripts/scripts_credentials.json', SCOPES) 
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('.credentials/scripts/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('script', 'v1', credentials=creds)

def run_apps_script():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/forms', 
              'https://www.googleapis.com/auth/spreadsheets']
    service = get_scripts_service()
    # PickEm project Scripts App API
    load_dotenv()
    API_ID = os.getenv('API_ID')
    request = {"function": "runProcess"}
    try:
        response = service.scripts().run(body=request, scriptId=API_ID).execute()
    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content)

## Date function
def get_week_season(dt):
    """
    function for returning the week of the NFL season
    :param dt: datetime object (can change input type if necessary)
    :return: tuple of (week number, year)
    """
    day_of_year = dt.timetuple().tm_yday
    # 252 was the day of year the season started
    # handling final weeks of season in 2022
    if day_of_year < 251:
        day_of_year += 365
    week_num = math.ceil((day_of_year - 251) / 7)
    return((dt.year, week_num))


# Cron run
today = datetime.date.today()
yr, wk_num = get_week_season(today)
run_export_process(week_num)
run_apps_script()




