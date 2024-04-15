import numpy as np
import pandas as pd
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
from openpyxl import Workbook

pd.options.display.width = None
pd.options.display.max_columns = None
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)
pd.options.display.float_format = '{:.2f}'.format

teams_abv = ['ATL', 'ARZ', 'BUF', 'BLT', 'CAR', 'CLV', 'CHI', 'CIN', 'DAL', 'DEN', 'DET', 'GB', 'HST', 'IND',
             'JAX', 'KC', 'LAC', 'LA', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF',
             'TB', 'TEN', 'WAS']

year = ['2020', '2021', '2022', '2023']

snaps_url = 'https://game-logs.api.ftntools.com/getSnapCountsReport?teamAbbv=SF&year=2023'
cap_url = 'https://www.spotrac.com/nfl/san-francisco-49ers/cap/2023/'

snaps = requests.get(url=snaps_url).json()
cap = requests.get(cap_url).text
soup = BeautifulSoup(cap, features="html.parser")

################################################################################################################
# test with Green Bay Packers 2023
# Finding the table
s = soup.find_all('table')
last_cap_hit = ['261110', '664379', '0', '3334']


# Getting the players list
# For table_count counter: 1) 53 roster 2) Injury reserve 3) Practice squad 4) Dead cap
def print_cap(table_count, sopa):
    pre_cap = sopa[table_count]
    cap_rows = pre_cap.find_all('span')
    name_list = pre_cap.find_all('a')

    n_list = []
    for name in name_list:
        n = name.get_text()
        n = n.replace(" Jr.", "")
        n = n.replace("La'Mical","Lamical")
        n = n.replace(" II", "")
        n = n.replace(" III", "")
        n = n.replace("Decobie", "Cobie")
        n = n.replace("Zach Thomas", "Zachary Thomas")
        n = n.replace("Rodríguez", "Rodriguez")
        n = n.replace("Dontavian", "Lucky")
        n = n.replace("Ta'Quon", "TaQuon")
        n = n.replace("Nathan", "Nate")
        #n = n.replace(" I", "")
        n = n.replace("Timothy", "Timmy")
        n = n.replace("Sebastian Joseph", "Sebastian Joseph-Day")
        n = n.replace("Scotty", "Scott")
        n = n.replace("Ugo", "Ugochukwu")
        n = n.replace("Nathan", "Nate")
        n = n.replace("DJ", "D.J.")
        n = n.replace("JL", "J.L.")
        n = n.replace("JT", "J.T.")
        n = n.replace("’", "'")
        n = n.replace("é", "e")
        n = n.replace("Chukwuma", "Chuks")
        n = n.replace("Michael", "Mike")
        n = n.replace("jordan", "Jordan")
        n = n.replace("Rodney", "Rod")
        n = n.replace("Ty Davis-Price", "Tyrion Davis-Price")
        #Wan'dale Robinson, Wan'Dale Robinson
        if "$" not in n:
            n_list.append(n)

    # Getting the cap hit list
    c_l = []
    for cap in cap_rows:
        c = cap.get_text()
        if "-" not in c:
            c_l.append(c)

    # we count form the 11th value in order to remove the header values of each table
    c_l = c_l[11:]
    cap_list = []
    for s in range(0, len(c_l)):
        text = str(c_l[s])
        if (text != '') and (ord(text[0]) in range(ord('A'), ord('Z'))):
            cap_list.append(c_l[s - 1])

    for n in cap_list:
        if n[0] != '$':
            cap_list.remove(n)

    # Removing the '$' symbol
    c_list = []
    for ca in cap_list:
        new_ca = ca.replace(",", "")
        new_ca = new_ca.replace(" ", "")
        c_list.append(new_ca[1:])

    # Adding the salary of the last player on each table
    c_list.append(last_cap_hit[table_count])

    # Creating the cap hit dataframe
    sub_cap_hit = pd.DataFrame(list(zip(n_list, c_list)), columns=['Player', 'Cap_Hit'])
    return sub_cap_hit


# Appending all the cap hit dataframes
sf_cap_space = []
for a in range(0, 4):
    append_df = print_cap(a, s)
    sf_cap_space.append(append_df)

sf_cap_space = pd.concat(sf_cap_space, ignore_index=True)
sf_cap_space['Cap_Hit'][57] = 1000038

################################################################################################################
# Table with player week snaps and salary as headers
df_columns = ['Player', 'Week', 'Snaps', 'Snaps_percentage']


# Method to obtain snaps per position
def print_snaps(position):
    df_data = pd.DataFrame(columns=df_columns)
    pre_column = snaps[position]
    x_q = 0
    for column in pre_column:
        df_row = [column['playername'], column['wk'], column['snaps'], column['snapperc']]
        df_row[0] = df_row[0].replace(" Jr.", "")
        df_row[0] = df_row[0].replace("Michael", "Mike")
        #n = n.replace("Michael", "Mike")
        if column['wk'] < 23:
            df_data.loc[x_q] = df_row
        x_q += 1

    snaps_df = pd.DataFrame(df_data, columns=df_columns).reset_index(drop=True)
    snaps_df['Snaps'] = snaps_df['Snaps'].astype(float)
    snaps_df['Snaps_percentage'] = snaps_df['Snaps_percentage'].astype(float)
    snaps_df['total_snaps'] = snaps_df['Snaps'] / snaps_df['Snaps_percentage']
    snaps_df['total_snaps'] = snaps_df['total_snaps'].fillna(0)
    snaps_df['total_snaps'] = snaps_df['total_snaps'].round()
    snaps_df['Snaps'] = snaps_df['Snaps'].astype(int)
    snaps_df['total_snaps'] = snaps_df['total_snaps'].astype(int)
    return snaps_df


# Obtaining qb_snaps
# We need qb snaps to obtain the reps of Jordan Love, the only player to play in all games on the offense
def offensive_snaps():
    of_snaps = []
    qb_snaps = print_snaps(0)
    s_w = qb_snaps['Week'].nunique(dropna=True)
    for wk in range(0, s_w):
        #qb_snaps['Snaps'][(2*s_w) + wk] +
        snp = qb_snaps['Snaps'][s_w + wk] + qb_snaps['Snaps'][wk]
        of_snaps.append(snp)

    return of_snaps


o_snaps = offensive_snaps()


# Obtaining dt snaps
# We need cb snaps to obtain the reps of Tedarrell Slaton, first defensive player on the list to play all games
def defensive_snaps():
    df_snaps = []
    dt_snaps = print_snaps(5)
    s_w = dt_snaps['Week'].nunique(dropna=True)
    n_p = int(dt_snaps['Player'].nunique(dropna=True))

    for i in range(0, (s_w * n_p)):
        name = dt_snaps['Player'][i]
        # Calais Campbell Larry Ogunjobi
        if name == "Kevin Givens":
            df_snaps.append(dt_snaps['total_snaps'][i])

    return df_snaps


d_snaps = defensive_snaps()


# Creating the dataset of snaps
def side_snaps(rang, side_snaps):
    snaps = []
    for a in rang:
        append_df = print_snaps(a)
        season_weeks = append_df['Week'].nunique(dropna=True)
        number_players = int(append_df['Player'].nunique(dropna=True))
        for p in range(0, number_players):
            for wk in range(0, season_weeks):
                append_df['total_snaps'][(season_weeks * p) + wk] = side_snaps[wk]
        append_df['Snaps_percentage'] = append_df['Snaps'] / append_df['total_snaps']
        append_df['Snaps_percentage'] = round(append_df['Snaps_percentage'], 3)
        snaps.append(append_df)

    snaps = pd.concat(snaps, ignore_index=True)
    return snaps


offense_range = range(0, 5)
defense_range = range(5, 11)
sf_offensive_snaps = side_snaps(offense_range, o_snaps)
sf_defensive_snaps = side_snaps(defense_range, d_snaps)
#print(sf_cap_space)
#print(sf_offensive_snaps)
#print(sf_defensive_snaps)

sf_snaps = pd.concat([sf_offensive_snaps, sf_defensive_snaps])
sf_snaps = sf_snaps.sort_values(by=['Snaps'], ascending=False)
sf_snaps = sf_snaps.sort_values(by=['Week']).reset_index(drop=True)

################################################################################################################
# Adding the cap hit column to the gb_snaps dataframe

sf_snaps['Cap_Hit'] = ""
for i in range(0, len(sf_snaps['Player'])):
    player = sf_snaps.iloc[i]['Player']
    cap_hit_index = sf_cap_space.index[sf_cap_space['Player'] == player].tolist()
    cap_hit_value = int(sf_cap_space.iloc[cap_hit_index[0]]['Cap_Hit'])
    sf_snaps['Cap_Hit'][i] = cap_hit_value

sf_snaps['Cap_Hit'] = sf_snaps['Cap_Hit'].astype(float)
sf_snaps['Cap_on_field'] = sf_snaps['Cap_Hit'] * sf_snaps['Snaps_percentage']
sf_snaps['Cap_Hit'] = sf_snaps['Cap_Hit'].astype(int)
sf_snaps['Cap_on_field'] = round(sf_snaps['Cap_on_field'], 2)

print(sf_snaps)
sf_snaps.to_excel('sf_snaps_cap_hit.xlsx', index=False)
