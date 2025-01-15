#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PS extract python script.
# (C) 2024
#
# Initial author: LD40
#
# SPDX-License-Identifier:    GPL-3.0-or-later license
"""
This program extracts data from Polarsteps JSON files, and allows to generate optionaly
- text file detailing steps
- local html files allowing to browse steps
- emails for each step to send to blogs to automaticaly generate articles
Static maps are also automaticaly generated to enhance presentation in local html and emails  
"""
import sys
import os
import datetime
from dateutil import tz
import json
import smtplib
import mimetypes
from pathlib import Path
from email.message import EmailMessage
from email.utils import formatdate
try : # if error while importing graphic library then map generation is disabled
    from PIL import Image
    import cairo
    import staticmaps
    gen_map = True
except:
    gen_map = False
    print("! Map generation module not available.")

# if these global email parameters are not set in the script they will be asked interactively when trying to send an email
dest_email =  '' 
orig_email = 'PS_extract@gmail.com' # enter here the email that you want to be displayed in email sent (it's not necessarily the email login used to connect to smtp server)
mail_serv = 'smtp.gmail.com' # you can change for any other email provider server
mail_port = 465 # change for smtp port your server expect to be called on
mail_login = '' # put here your email login
mail_passwd = '' # put here your password - for gmail should be an App password (16 letters)

# other global parameters
extract_dir = "Extracts"
no_location = True # suppose there are no locations until json is parsed

# set all specific run modes of the script to False ; should be modified through launching args 
mail = False
local = False
interactive = False
verbose = False
exclude = False


# Function to generate map using tile name in parameter (allowed tiles by staticmaps listed bellow)
if gen_map: 
    def tile(style = staticmaps.tile_provider_OSM):
        map = staticmaps.Context()
        map.set_tile_provider(style)
            #staticmaps.tile_provider_OSM,
            #staticmaps.tile_provider_ArcGISWorldImagery,
            #staticmaps.tile_provider_CartoNoLabels,
            #staticmaps.tile_provider_CartoDarkNoLabels,
            #staticmaps.tile_provider_None,        
            #not working#staticmaps.tile_provider_StamenTerrain,
            #not working#staticmaps.tile_provider_StamenToner,
            #not working#staticmaps.tile_provider_StamenTonerLite,  
        return map

# Function to send email message in parameter
def email(msg):
    # get global parameters
    global dest_email
    global orig_email
    global mail_serv
    global mail_port
    global mail_login
    global mail_passwd
    # ask for undefined parameters
    if dest_email == "": dest_email = input(f"--> Input destination address where emails should be sent (i.e. myblog.mywp.com): ") 
    if orig_email == "": orig_email = input(f"--> Input email address you want to appear in sent emails (i.e. myaddress.myisp.com): ") 
    if mail_serv == "": mail_serv = input(f"--> Input email server that should be used to send emails (i.e. smtp.myisp.com): ") 
    if mail_port == "": mail_port = input(f"--> Input email server port that should be used to send emails (i.e. 465 or 587 or 25): ") 
    if mail_login == "": mail_login = input(f"--> Input email login that should be used to send emails (i.e. myname@myisp.com): ") 
    if mail_passwd == "": mail_passwd = input(f"-->Input email password that should be used to send emails: ") 
    if msg['From'] == None: msg['From'] = orig_email
    if msg['To'] == None: msg['To'] = ', '.join([dest_email])
    try:
        # use SSL connexion ; for gmail ensure that you use an App password and not your regular password
        mail_server = smtplib.SMTP_SSL(mail_serv,mail_port) 
        mail_server.ehlo() 
        mail_server.login(mail_login, mail_passwd)
        mail_server.send_message(msg)
        print(f"Email {msg['Subject']} sent to {dest_email}.\n")
        mail_server.quit()
    except smtplib.SMTPException as e:
        print(e)
    return

   
# Function to parse data and generate different items depending on options selected  
def parse_data(data, original_path, extract_dir):
    
    # Function to return last modification time of the file in parameter
    def get_modif_time(entry):
        return entry.stat().st_mtime
        
    # get global parameters
    global mail
    global local
    global interactive
    global verbose
    global exclude
    global no_location
    # define table to use special UTF-8 characters (emoticon) to weather conditions and countries
    weather_dict = {"rain":"\U0001F327","clear-day":"\U0001F506","partly-cloudy-day":"\U000026C5","snow":"\U000026C4","cloudy":"\U00002601"}
    country_dict = { #these countries denominations have been tested as used by PS in 2024/07
"Andorra":"\U0001F1E6\U0001F1E9","United Arab Emirates":"\U0001F1E6\U0001F1EA","Afghanistan":"\U0001F1E6\U0001F1EB","Antigua and Barbuda":"\U0001F1E6\U0001F1EC","Anguilla":"\U0001F1E6\U0001F1EE","Albania":"\U0001F1E6\U0001F1F1","Armenia":"\U0001F1E6\U0001F1F2","Angola":"\U0001F1E6\U0001F1F4","Antarctica":"\U0001F1E6\U0001F1F6","Argentina":"\U0001F1E6\U0001F1F7","Austria":"\U0001F1E6\U0001F1F9","Australia":"\U0001F1E6\U0001F1FA","Azerbaijan":"\U0001F1E6\U0001F1FF","Bosnia and Herzegovina":"\U0001F1E7\U0001F1E6","Barbados":"\U0001F1E7\U0001F1E7","Bangladesh":"\U0001F1E7\U0001F1E9","Belgium":"\U0001F1E7\U0001F1EA","Burkina Faso":"\U0001F1E7\U0001F1EB","Bulgaria":"\U0001F1E7\U0001F1EC","Bahrain":"\U0001F1E7\U0001F1ED","Burundi":"\U0001F1E7\U0001F1EE","Benin":"\U0001F1E7\U0001F1EF","Saint Barthelemy":"\U0001F1E7\U0001F1F1","Bermuda":"\U0001F1E7\U0001F1F2","Brunei":"\U0001F1E7\U0001F1F3","Bolivia":"\U0001F1E7\U0001F1F4","Brazil":"\U0001F1E7\U0001F1F7","Bahamas":"\U0001F1E7\U0001F1F8","Bhutan":"\U0001F1E7\U0001F1F9","Botswana":"\U0001F1E7\U0001F1FC","Belarus":"\U0001F1E7\U0001F1FE","Belize":"\U0001F1E7\U0001F1FF","Canada":"\U0001F1E8\U0001F1E6","Democratic Republic of the Congo":"\U0001F1E8\U0001F1E9","Central African Republic":"\U0001F1E8\U0001F1EB","Congo":"\U0001F1E8\U0001F1EC","Switzerland":"\U0001F1E8\U0001F1ED","Côte d'Ivoire":"\U0001F1E8\U0001F1EE","Cook Islands":"\U0001F1E8\U0001F1F0","Chile":"\U0001F1E8\U0001F1F1","Cameroon":"\U0001F1E8\U0001F1F2","China":"\U0001F1E8\U0001F1F3","Colombia":"\U0001F1E8\U0001F1F4","Costa Rica":"\U0001F1E8\U0001F1F7","Cuba":"\U0001F1E8\U0001F1FA","Cape Verde":"\U0001F1E8\U0001F1FB","Curacao":"\U0001F1E8\U0001F1FC","Cyprus":"\U0001F1E8\U0001F1FE","Czechia":"\U0001F1E8\U0001F1FF","Germany":"\U0001F1E9\U0001F1EA","Djibouti":"\U0001F1E9\U0001F1EF","Denmark":"\U0001F1E9\U0001F1F0","Dominica":"\U0001F1E9\U0001F1F2","Dominican Republic":"\U0001F1E9\U0001F1F4","Algeria":"\U0001F1E9\U0001F1FF","Ecuador":"\U0001F1EA\U0001F1E8","Estonia":"\U0001F1EA\U0001F1EA","Egypt":"\U0001F1EA\U0001F1EC","Sahrawi Arab Democratic Republic":"\U0001F1EA\U0001F1ED","Eritrea":"\U0001F1EA\U0001F1F7","Spain":"\U0001F1EA\U0001F1F8","Ethiopia":"\U0001F1EA\U0001F1F9","Finland":"\U0001F1EB\U0001F1EE","Fiji":"\U0001F1EB\U0001F1EF","Falkland Islands":"\U0001F1EB\U0001F1F0","Federated States of Micronesia":"\U0001F1EB\U0001F1F2","Faroe Islands":"\U0001F1EB\U0001F1F4","France":"\U0001F1EB\U0001F1F7","Gabon":"\U0001F1EC\U0001F1E6","United Kingdom":"\U0001F1EC\U0001F1E7","Grenada":"\U0001F1EC\U0001F1E9","Georgia":"\U0001F1EC\U0001F1EA","Guernsey":"\U0001F1EC\U0001F1EC","Ghana":"\U0001F1EC\U0001F1ED","Gibraltar":"\U0001F1EC\U0001F1EE","Greenland":"\U0001F1EC\U0001F1F1","The Gambia":"\U0001F1EC\U0001F1F2","Guinea":"\U0001F1EC\U0001F1F3","Equatorial Guinea":"\U0001F1EC\U0001F1F6","Greece":"\U0001F1EC\U0001F1F7","South Georgia and the South Sandwich Islands":"\U0001F1EC\U0001F1F8","Guatemala":"\U0001F1EC\U0001F1F9","Guinea-Bissau":"\U0001F1EC\U0001F1FC","Guyana":"\U0001F1EC\U0001F1FE","Hong Kong":"\U0001F1ED\U0001F1F0","Honduras":"\U0001F1ED\U0001F1F3","Croatia":"\U0001F1ED\U0001F1F7","Haiti":"\U0001F1ED\U0001F1F9","Hungary":"\U0001F1ED\U0001F1FA","Indonesia":"\U0001F1EE\U0001F1E9","Ireland":"\U0001F1EE\U0001F1EA","Israel":"\U0001F1EE\U0001F1F1","Isle of Man":"\U0001F1EE\U0001F1F2","India":"\U0001F1EE\U0001F1F3","British Indian Ocean Territory":"\U0001F1EE\U0001F1F4","Iraq":"\U0001F1EE\U0001F1F6","Iran":"\U0001F1EE\U0001F1F7","Iceland":"\U0001F1EE\U0001F1F8","Italy":"\U0001F1EE\U0001F1F9","Jersey":"\U0001F1EF\U0001F1EA","Jamaica":"\U0001F1EF\U0001F1F2","Jordan":"\U0001F1EF\U0001F1F4","Japan":"\U0001F1EF\U0001F1F5","Kenya":"\U0001F1F0\U0001F1EA","Kyrgyzstan":"\U0001F1F0\U0001F1EC","Cambodia":"\U0001F1F0\U0001F1ED","Kiribati":"\U0001F1F0\U0001F1EE","Comoros":"\U0001F1F0\U0001F1F2","Saint Kitts and Nevis":"\U0001F1F0\U0001F1F3","North Korea":"\U0001F1F0\U0001F1F5","South Korea":"\U0001F1F0\U0001F1F7","Kuwait":"\U0001F1F0\U0001F1FC","Cayman Islands":"\U0001F1F0\U0001F1FE","Kazakhstan":"\U0001F1F0\U0001F1FF","Laos":"\U0001F1F1\U0001F1E6","Lebanon":"\U0001F1F1\U0001F1E7","Saint Lucia":"\U0001F1F1\U0001F1E8","Liechtenstein":"\U0001F1F1\U0001F1EE","Sri Lanka":"\U0001F1F1\U0001F1F0","Liberia":"\U0001F1F1\U0001F1F7","Lesotho":"\U0001F1F1\U0001F1F8","Lithuania":"\U0001F1F1\U0001F1F9","Luxembourg":"\U0001F1F1\U0001F1FA","Latvia":"\U0001F1F1\U0001F1FB","Libya":"\U0001F1F1\U0001F1FE","Morocco":"\U0001F1F2\U0001F1E6","Monaco":"\U0001F1F2\U0001F1E8","Moldova":"\U0001F1F2\U0001F1E9","Montenegro":"\U0001F1F2\U0001F1EA","Saint Martin":"\U0001F1F2\U0001F1EB","Madagascar":"\U0001F1F2\U0001F1EC","Marshall Islands":"\U0001F1F2\U0001F1ED","North Macedonia":"\U0001F1F2\U0001F1F0","Mali":"\U0001F1F2\U0001F1F1","Myanmar":"\U0001F1F2\U0001F1F2","Mongolia":"\U0001F1F2\U0001F1F3","Mauritania":"\U0001F1F2\U0001F1F7","Montserrat":"\U0001F1F2\U0001F1F8","Malta":"\U0001F1F2\U0001F1F9","Mauritius":"\U0001F1F2\U0001F1FA","Maldives":"\U0001F1F2\U0001F1FB","Malawi":"\U0001F1F2\U0001F1FC","Mexico":"\U0001F1F2\U0001F1FD","Malaysia":"\U0001F1F2\U0001F1FE","Mozambique":"\U0001F1F2\U0001F1FF","Namibia":"\U0001F1F3\U0001F1E6","New Caledonia":"\U0001F1F3\U0001F1E8","Niger":"\U0001F1F3\U0001F1EA","Norfolk Island":"\U0001F1F3\U0001F1EB","Nigeria":"\U0001F1F3\U0001F1EC","Nicaragua":"\U0001F1F3\U0001F1EE","Netherlands":"\U0001F1F3\U0001F1F1","Norway":"\U0001F1F3\U0001F1F4","Nepal":"\U0001F1F3\U0001F1F5","Nauru":"\U0001F1F3\U0001F1F7","Niue":"\U0001F1F3\U0001F1FA","New Zealand":"\U0001F1F3\U0001F1FF","Oman":"\U0001F1F4\U0001F1F2","Panama":"\U0001F1F5\U0001F1E6","Peru":"\U0001F1F5\U0001F1EA","Papua New Guinea":"\U0001F1F5\U0001F1EC","Philippines":"\U0001F1F5\U0001F1ED","Pakistan":"\U0001F1F5\U0001F1F0","Poland":"\U0001F1F5\U0001F1F1","Pitcairn Islands":"\U0001F1F5\U0001F1F3","Puerto Rico":"\U0001F1F5\U0001F1F7","Palestinian Territory":"\U0001F1F5\U0001F1F8","Portugal":"\U0001F1F5\U0001F1F9","Palau":"\U0001F1F5\U0001F1FC","Paraguay":"\U0001F1F5\U0001F1FE","Qatar":"\U0001F1F6\U0001F1E6","Romania":"\U0001F1F7\U0001F1F4","Serbia":"\U0001F1F7\U0001F1F8","Russia":"\U0001F1F7\U0001F1FA","Rwanda":"\U0001F1F7\U0001F1FC","Saudi Arabia":"\U0001F1F8\U0001F1E6","Solomon Islands":"\U0001F1F8\U0001F1E7","Seychelles":"\U0001F1F8\U0001F1E8","Sudan":"\U0001F1F8\U0001F1E9","Sweden":"\U0001F1F8\U0001F1EA","Singapore":"\U0001F1F8\U0001F1EC","Saint Helena, Ascension and Tristan da Cunha":"\U0001F1F8\U0001F1ED","Slovenia":"\U0001F1F8\U0001F1EE","Slovakia":"\U0001F1F8\U0001F1F0","Sierra Leone":"\U0001F1F8\U0001F1F1","San Marino":"\U0001F1F8\U0001F1F2","Senegal":"\U0001F1F8\U0001F1F3","Somalia":"\U0001F1F8\U0001F1F4","Suriname":"\U0001F1F8\U0001F1F7","South Sudan":"\U0001F1F8\U0001F1F8","São Tomé and Príncipe":"\U0001F1F8\U0001F1F9","El Salvador":"\U0001F1F8\U0001F1FB","Sint Maarten":"\U0001F1F8\U0001F1FD","Syria":"\U0001F1F8\U0001F1FE","eSwatini":"\U0001F1F8\U0001F1FF","Turks and Caicos Islands":"\U0001F1F9\U0001F1E8","Chad":"\U0001F1F9\U0001F1E9","French Southern and Antarctic Lands":"\U0001F1F9\U0001F1EB","Togo":"\U0001F1F9\U0001F1EC","Thailand":"\U0001F1F9\U0001F1ED","Tajikistan":"\U0001F1F9\U0001F1EF","Tokelau":"\U0001F1F9\U0001F1F0","East Timor":"\U0001F1F9\U0001F1F1","Turkmenistan":"\U0001F1F9\U0001F1F2","Tunisia":"\U0001F1F9\U0001F1F3","Tonga":"\U0001F1F9\U0001F1F4","Turkey":"\U0001F1F9\U0001F1F7","Trinidad and Tobago":"\U0001F1F9\U0001F1F9","Tuvalu":"\U0001F1F9\U0001F1FB","Taiwan":"\U0001F1F9\U0001F1FC","Tanzania":"\U0001F1F9\U0001F1FF","Ukraine":"\U0001F1FA\U0001F1E6","Uganda":"\U0001F1FA\U0001F1EC","USA":"\U0001F1FA\U0001F1F8","Uruguay":"\U0001F1FA\U0001F1FE","Uzbekistan":"\U0001F1FA\U0001F1FF","Vatican City":"\U0001F1FB\U0001F1E6","Saint Vincent and the Grenadines":"\U0001F1FB\U0001F1E8","Venezuela":"\U0001F1FB\U0001F1EA","British Virgin Islands":"\U0001F1FB\U0001F1EC","US Virgin Islands":"\U0001F1FB\U0001F1EE","Vietnam":"\U0001F1FB\U0001F1F3","Vanuatu":"\U0001F1FB\U0001F1FA","Samoa":"\U0001F1FC\U0001F1F8","Kosovo":"\U0001F1FD\U0001F1F0","Yemen":"\U0001F1FE\U0001F1EA","South Africa":"\U0001F1FF\U0001F1E6","Zambia":"\U0001F1FF\U0001F1F2","Zimbabwe":"\U0001F1FF\U0001F1FC",
# additional denominations not identified as used by PS
"American Samoa":"\U0001F1E6\U0001F1F8","Aruba":"\U0001F1E6\U0001F1FC","Åland Islands":"\U0001F1E6\U0001F1FD","Bonaire, Sint Eustatius and Saba":"\U0001F1E7\U0001F1F6","Bouvet Island":"\U0001F1E7\U0001F1FB","Cocos (Keeling) Islands":"\U0001F1E8\U0001F1E8","Christmas Island":"\U0001F1E8\U0001F1FD","French Guiana":"\U0001F1EC\U0001F1EB","Guadeloupe":"\U0001F1EC\U0001F1F5","Guam":"\U0001F1EC\U0001F1FA","Heard Island and Mcdonald Islands":"\U0001F1ED\U0001F1F2","Macao":"\U0001F1F2\U0001F1F4","Northern Mariana Islands":"\U0001F1F2\U0001F1F5","Martinique":"\U0001F1F2\U0001F1F6","French Polynesia":"\U0001F1F5\U0001F1EB","Saint Pierre and Miquelon":"\U0001F1F5\U0001F1F2","Réunion":"\U0001F1F7\U0001F1EA","Svalbard and Jan Mayen":"\U0001F1F8\U0001F1EF","United States Minor Outlying Islands":"\U0001F1FA\U0001F1F2","Wallis and Futuna":"\U0001F1FC\U0001F1EB","Mayotte":"\U0001F1FE\U0001F1F9"}
    
    # define CSS file that will be created for local html generation
    css_text = """
html, body {
    font-family: arial;
    padding: 0 2em;
    font-size: 18px;
    background: #111;
    color: #aaa;
    text-align:center;
}

h1 {
    font-size: 3em;
    font-weight: 100;
}

h2 {
    margin-bottom: 1px;
}

p {
    font-weight: 100;
    color: #888;
    margin-bottom: 20px;
}

small {
    font-size: 0.5em;
}

.footer { 
    font-style: italic;
    margin-top: 45px;
}

a {
    text-decoration: none;
}

.thumb {
    max-height: 180px;
    border: solid 6px rgba(5, 5, 5, 0.8);
}

.thumb-vid {
    max-height: 180px;
    border: solid 6px rgba(105, 105, 105, 0.5);
    opacity: 0.5;
}

.lightbox {
    position: fixed;
    z-index: 999;
    height: 0;
    width: 0;
    text-align: center;
    top: 0;
    left: 0;
    background: rgba(0, 0, 0, 0.8);
    opacity: 0;
}

.lightbox img {
    max-width: 95%;
    max-height: 90%;
    margin-top: 2%;
    opacity: 0;
}

.lightbox video {
    max-width: 95%;
    max-height: 90%;
    margin-top: 2%;
    opacity: 0;
}

.lightbox:target {
    /** Remove default browser outline */
    outline: none;
    width: 100%;
    height: 100%;
    opacity: 1 !important;
}

.lightbox:target img {
    border: solid 10px rgba(77, 77, 77, 0.8);
    opacity: 1;
    webkit-transition: opacity 0.6s;
    transition: opacity 0.6s;
}

.lightbox:target video {
    border: solid 10px rgba(77, 77, 77, 0.8);
    opacity: 1;
    webkit-transition: opacity 0.6s;
    transition: opacity 0.6s;
}

.light-btn {
    color: #fafafa;
    background-color: #333;
    border: solid 3px #777;
    padding: 5px 10px;
    border-radius: 1px;
    text-decoration: none;
    cursor: pointer;
    vertical-align: middle;
    position: absolute;
    top: 45%;
    z-index: 99;
}

.light-btn:hover {
    background-color: #111;
}

.btn-prev {
    left: 7%;
}

.btn-next {
    right: 7%;
}

.btn-close {
    position: absolute;
    right: 2%;
    top: 2%;
    color: #fafafa;
    background-color: #92001d;
    border: solid 3px #777;
    padding: 5px 10px;
    border-radius: 1px;
    text-decoration: none;
}

.btn-close:hover {
    background-color: #740404;
}
"""

    # get general information about the trip
    trip_name = data['name'].strip()
    trip_summary = data['summary']
    trip_start_date = datetime.datetime.fromtimestamp(data['start_date']).strftime('%Y-%m-%d')
    if data['end_date'] != None: trip_end_date = datetime.datetime.fromtimestamp(data['end_date']).strftime('%Y-%m-%d')
    else: trip_end_date = "?"
    total_distance = data['total_km']
    if data['travel_tracker_device'] != None: phone_type = data['travel_tracker_device']['device_name']
    else: phone_type = "?"
    timezone_id = data['timezone_id']
    total_entries = data['step_count']
    
    # initialize global map
    if gen_map: global_map = tile(staticmaps.tile_provider_ArcGISWorldImagery)
    # create .txt file
    file_out = f"{extract_dir}{os.sep}{trip_name}_{trip_start_date}.txt"
    with open(file_out,'w', encoding="utf-8") as f_out:
        if local: # create css and index.htm file
            css_file = open(f"{extract_dir}{os.sep}local.css",'w', encoding="utf-8")
            css_file.write(css_text)
            css_file.close()
            index_file = open(f"{extract_dir}{os.sep}index.htm",'w', encoding="utf-8")
            index_file.write(f"<head>\n    <link rel=\"stylesheet\" type=\"text/css\" href=\"local.css\">\n</head>\n<body>\n<h1>{trip_name}</h1>\n<p id=intro>")
            index_file.write(f"{trip_summary}, {round(total_distance)}km, {total_entries} steps, {trip_start_date}-{trip_end_date}\n<br><br>\n")
            if gen_map: index_file.write(f"<img src=\"steps_map.png\"></p>\n")
        text = f"Trip Name: {trip_name}\n{trip_summary}\n"
        text += f"Start Date: {trip_start_date}\nEnd Date: {trip_end_date}\n"
        text += f"Total Distance: {round(total_distance)}(km) in {total_entries} steps\n"
        if verbose: text += f"User Timezone: {timezone_id}\nRecording Device: {phone_type}\n"
        text += "____________________\n"
        if interactive: print(text)
        f_out.write(text+"\n")       
        from_zone = tz.gettz('UTC')
        # loop on each step of the trip
        for step_num, entry in enumerate(data['all_steps']):
            # get step information
            step_id = entry['id']
            step_slug = entry['slug']
            step_name = entry['display_name']
            to_zone = tz.gettz(timezone_id)
            # prefer start time of the step than the creation time in PS as the time of teh step to be displayed
            creation_time = datetime.datetime.fromtimestamp(entry['start_time'])
            creation_time = creation_time.replace(tzinfo = from_zone)
            adjusted_time = creation_time.astimezone(to_zone)
            adjusted_date = adjusted_time.strftime('%Y-%m-%d')
            # get location information
            location_name = entry['location']['name']
            location_lat = entry['location']['lat']
            location_lon = entry['location']['lon']
            location_country = entry['location']['detail']
            location_detail = entry['location']['full_detail']
            # if possible replace location text by corresponding flag
            if location_country in country_dict:
                country = country_dict[location_country]
                if location_detail != location_country: country = country + " "+location_detail.split(",")[0]
                # print(f"Flag for country '{location_country}' detected")
            else: 
                country = location_detail
                print(f"! Flag for country '{location_country}' not present !")
            # get weather condition and if possible replace weather text by corresponding emoticon
            weather_condition = entry['weather_condition']
            weather = weather_dict[weather_condition] if weather_condition in weather_dict else weather_condition
            temperature = entry['weather_temperature']
            # get step description
            journal = entry['description'] if entry['description'] != None else ""
            # generate text for .txt file
            text = f"Step: {step_name}\n"
            if verbose: text += f"Step Id: {step_id}, Slug: {step_slug}\n"
            text += f"Date: {adjusted_time.strftime('%Y-%m-%d %H:%M')}\n"
            if verbose: text += f"Location: {country} {location_name} ({location_lat},{location_lon} - {location_detail})"
            text += f"\nWeather: {weather_condition}, Temperature: {temperature}°C\n\n"
            text += f"{journal}\n\n"      
            if local: # generate html content
                index_file.write(f"<h2>{step_name} <small>{adjusted_date}</small></h2><a href=\"{step_id}.htm\">\n")
                # create step related html file
                step_file = open(f"{extract_dir}{os.sep}{step_id}.htm",'w', encoding="utf-8")
                step_file.write(f"<head>\n    <link rel=\"stylesheet\" type=\"text/css\" href=\"local.css\">\n</head>\n<body>\n<h1>{step_name}</h1>\n<p id=intro>{country} {location_name} \U0001F538 {adjusted_date} \U0001F538 {weather}")
                if temperature != None: step_file.write(f" {int(temperature)}°C")
                step_file.write(f"\n<br><br>")
            # generate email structure
            msg = EmailMessage()
            msg['Subject'] = step_name
            msg["Date"] = adjusted_time
            mess = f"{country} {location_name} \U0001F538 {weather}"
            if temperature != None: mess += f"{int(temperature)}°C"
            mess += f"\n\n{journal}\n"
            msg.set_content(mess)
            # initialize counters before parsing photos and videos related to this step
            photos_nbr = 0
            videos_nbr = 0
            total_size = 0
            new_total_size = 0
            step_image = ""
            # get the list of photos and sort them to try to retrieve PS order
            path = f"{original_path}\\{step_slug}_{step_id}\\photos"
            if os.path.isdir(path):
                with os.scandir(path) as entries:
                    sorted_entries = sorted(entries, key=get_modif_time)
                    sorted_photos = [entry.name for entry in sorted_entries]
                    if "Thumbs.db" in sorted_photos: sorted_photos.remove("Thumbs.db")
                    photos_nbr = len(sorted_photos)
            # get the list of videos and sort them to try to retrieve PS order
            path = f"{original_path}\\{step_slug}_{step_id}\\videos"
            if os.path.isdir(path):
                with os.scandir(path) as entries:
                    sorted_entries = sorted(entries, key=get_modif_time)
                    sorted_videos = [entry.name for entry in sorted_entries]
                    videos_nbr = len(sorted_videos)
            # parse photos
            if photos_nbr > 0: 
                for photo, f in enumerate(sorted_photos):
                    cfile = Path(f"{os.getcwd()}\\{step_slug}_{step_id}\\photos\\{f}")
                    initial_size = cfile.stat().st_size
                    if verbose: text += f"Photo {photo+1}: {f} ({round(initial_size/1024/102.4)/10}Mb"
                    ctype, encoding = mimetypes.guess_type(cfile)
                    if ctype is None or encoding is not None: ctype = 'image/jpeg'
                    maintype, subtype = ctype.split('/', 1)
                    total_size = total_size + initial_size
                    image = Image.open(cfile)
                    width, height = image.size 
                    if local: # add photo (in gallery mode) to the step html file and previous/next links
                        step_file.write(f"<a href=\"#img{photo+1}\"><img class=\"thumb\" src=\"..\\{step_slug}_{step_id}\\photos\\{f}\"></a>\n")
                        step_file.write(f"<div class=\"lightbox\" id=\"img{photo+1}\">\n")
                        if photo > 0: step_file.write(f"<a href=\"#img{photo}\" class=\"light-btn btn-prev\"><</a>\n")
                        else: step_image = f"..\\{step_slug}_{step_id}\\photos\\{f}"
                        step_file.write(f"<a href=\"#_\" class=\"btn-close\">X</a>\n<img src=\"..\\{step_slug}_{step_id}\\photos\\{f}\">\n")
                        if photo+1 < photos_nbr: step_file.write(f"<a href=\"#img{photo+2}\" class=\"light-btn btn-next\">></a>\n</div>\n")
                        elif videos_nbr > 0: step_file.write(f"<a href=\"#vid1\" class=\"light-btn btn-next\">></a>\n</div>\n")
                        else: step_file.write(f"</div>\n")
                    # generated resized image to limit size to be sent by email if necessary
                    if (mail or interactive) and height > 800:
                        ratio = height / width
                        new_height = 800
                        new_width = int(new_height / ratio)
                        resized_img = image.resize((new_width, new_height), Image.LANCZOS)
                        resized_img.save(extract_dir+os.sep+'tmp.jpg') 
                        new_size = Path(extract_dir+os.sep+'tmp.jpg').stat().st_size
                        new_total_size = new_total_size + new_size
                        if verbose: text += f" compressible to {round(new_size/1024/102.4)/10}Mb"
                        cfile = Path(f"{extract_dir}{os.sep}tmp.jpg")
                    else: new_total_size = new_total_size + initial_size
                    if verbose: text += ")\n"                  
                    if (mail or interactive): msg.add_attachment(cfile.read_bytes(), maintype=maintype, subtype=subtype, filename=f"img_{step_id}_{photo+1}")
            # parse videos
            if videos_nbr > 0: 
                for video,f in enumerate(sorted_videos):
                    cfile = Path(f"{os.getcwd()}\\{step_slug}_{step_id}\\videos\\{f}")
                    initial_size = cfile.stat().st_size
                    if verbose: text += f"Video {video}: {f} ({round(initial_size/1024/102.4)/10}Mb)\n"
                    ctype, encoding = mimetypes.guess_type(cfile)
                    if ctype is None or encoding is not None: ctype = 'video/mp4'
                    maintype, subtype = ctype.split('/', 1)
                    total_size = total_size + initial_size
                    new_total_size = new_total_size + initial_size
                    if local: # add video (in gallery mode) to the step html file and previous/next links
                        step_file.write(f"<a href=\"#vid{video+1}\"><video class=\"thumb-vid\" src=\"..\\{step_slug}_{step_id}\\videos\\{f}\"></video></a>\n")
                        step_file.write(f"<div class=\"lightbox\" id=\"vid{video+1}\">\n")
                        if video > 0: step_file.write(f"<a href=\"#vid{video-1}\" class=\"light-btn btn-prev\"><</a>\n")
                        else:
                            if step_image == "": step_image = f"..\\{step_slug}_{step_id}\\videos\\{f}"
                            if photos_nbr > 0: step_file.write(f"<a href=\"#img{photos_nbr}\" class=\"light-btn btn-prev\"><</a>\n")
                        step_file.write(f"<a href=\"#_\" class=\"btn-close\">X</a>\n<video controls src=\"..\\{step_slug}_{step_id}\\videos\\{f}\"></video>\n")
                        if video+1 < videos_nbr: step_file.write(f"<a href=\"#vid{video+2}\" class=\"light-btn btn-next\">></a>\n</div>\n")
                        else: step_file.write(f"</div>\n")
                    if (mail or interactive): msg.add_attachment(cfile.read_bytes(), maintype=maintype, subtype=subtype, filename=f"vid_{step_id}_{video+1}")
            text += f"{photos_nbr} photo(s), {videos_nbr} video(s) ({round(total_size/1024/102.4)/10}Mb"
            if (mail or interactive): text += f" compressible to {round(new_total_size/1024/102.4)/10}Mb"
            text += ")\n____________________\n"
            if interactive: print(text)
            f_out.write(f"{text}\n")
            # generate map for the step with only a marker on the step location
            if gen_map:
                step_map = tile(staticmaps.tile_provider_OSM)
                step_map.set_zoom(6) # define static zoom level
                step_map.add_object(staticmaps.Marker(staticmaps.create_latlng(location_lat, location_lon), size=10))
                map_image = step_map.render_cairo(300, 200) # define 300x200 pixel size for the image
                map_name = f"map_{step_id}.png"
                map_image.write_to_png(f"{extract_dir}{os.sep}{map_name}")
            if local: # generate step html file
                if gen_map: index_file.write(f"<img class=\"thumb\" src=\"{map_name}\"> ") # add map to local html index file
                if photos_nbr > 0: index_file.write(f"<img class=\"thumb\" src=\"{step_image}\">\n")
                elif videos_nbr > 0: index_file.write(f"<video controls class=\"thumb\" src=\"{step_image}\">\n")
                index_file.write(f"</a><br>\n")
                step_file.write(f"<p class=\"footer\">\n")
                if step_num > 0: step_file.write(f"< <a href=\"{data['all_steps'][step_num-1]['id']}.htm\">{data['all_steps'][step_num-1]['display_name']}</a> | ")
                step_file.write(f"<a href=\"index.htm\">{trip_name}</a>")
                if step_num <total_entries-1: step_file.write(f" | <a href=\"{data['all_steps'][step_num+1]['id']}.htm\">{data['all_steps'][step_num+1]['display_name']}</a> >")
                step_file.write(f"</p>\n</body>\n")
                step_file.close()
            if gen_map: msg.add_attachment(Path(f"{extract_dir}{os.sep}{map_name}").read_bytes(), maintype='image', subtype='png', filename=map_name)
            # if exclude option is activated, skip first and last step. this avoid to add in the global map far origin for the travel
            if gen_map:
                if (not exclude or (step_num!=0 and step_num!=len(data['all_steps'])-1)): 
                    global_map.add_object(staticmaps.Marker(staticmaps.create_latlng(location_lat, location_lon), size=10))
                else: print(f"Skipping marker addition for step {step_num+1} ({round(location_lat,1)},{round(location_lon,1)}) in global map")
            # if interactive mode is active, it will ask what to do for each step
            if interactive:
                action = input(f"--> Action for step {step_num+1} [{step_name}] ? (s)kip (default), (e)mail, (q)uit ? ")
                if action =="q" or action == "quit": 
                    print("...exiting")
                    return
                elif action =="e" or action =="email":
                    print("...mailing this step")
                    email(msg) 
                elif action =="s" or action=="skip" or action=="": 
                    print("...jumping to next step")
                else: 
                    print("...resuming")
                    if mail: email(msg)
            elif mail: email(msg)
    # close .txt file
    f_out.close()
    if os.path.exists(f"{extract_dir}{os.sep}tmp.jpg"): os.remove(f"{extract_dir}{os.sep}tmp.jpg")
    if local: # add map to local index html file and close it
        if gen_map and not no_location: index_file.write(f"<br><br>\n<img src=\"trip_map.png\">")
        index_file.write("</p>\n</body>\n")
        index_file.close()
    # finish global map generation for the travel in 800x600 pixels size
    if gen_map:
        global_map_image = global_map.render_cairo(800, 600)
        global_map_image.write_to_png(f"{extract_dir}{os.sep}steps_map.png")
    if mail or interactive: # generate global trip email
        if interactive:
            action = input("-->Generate global trip email ? (y)es, (n)o ? ")
            if action == "n" or action == "no": return
        msg = EmailMessage()
        msg['Subject'] = trip_name
        to_zone = tz.gettz(timezone_id)
        creation_time = datetime.datetime.fromtimestamp(data['start_date'])
        creation_time = creation_time.replace(tzinfo = from_zone) # mark the TZ as UTC
        msg["Date"] = creation_time.astimezone(to_zone)
        mess = f"{trip_summary}\n{country} {round(total_distance)}km, {total_entries} steps, {trip_start_date}-{trip_end_date}\n"
        msg.set_content(mess)
        if gen_map: msg.add_attachment(Path(f"{extract_dir}{os.sep}steps_map.png").read_bytes(), maintype='image', subtype='png', filename=f"map_{trip_name}.png")
        email(msg)

# Function to print instructions of the script
def printInstructions():
    print("""
Usage: unzip your Polarsteps data, then navigate to the directory/folder of the trip you want to extract. You should see trip.json and locations.json files in it.
For easy use, copy extract.py script in that place.

Run this program with the following command :
    python3 (/path_to_program_directory/)extract.py [options]
The program will create an 'Extracts' directory and extract in it all informations from your Polarsteps data in a readable text file (.txt), and some automatically generated static maps (PNG files) of your trip and steps.
In addition, you can ask to generate localy browsable HTML pages to navigate trough your steps, and/or generate emails for each steps (with text, images and videos from your steps). It is possible to extract data step by step in interactive mode, or to generate all files for the whole trip.

Here are the additional options that could be combined and put at launch:
-v, -verbose :                  to add additional information in the generated text file
-l, -local :                    to generate local html files to navigate the steps
-e, -email address@domain.com : to send emails containing description, images and videos from extracted steps to the given address (for example to fill a blog like blogger or wordpress using postie plugin) ; consider putting your common email server parameters directly in the script to avoid having to type them everytime you execute the script
-i, -interactive :              to display an analysis and interactively ask what to do for each step (skip, email, continue or quit)
-x, -exclude :                  to exclude the first and last steps from generated maps presenting the whole trip (allow to focus the map when origin country is far away)
anything else will display this help
""")


# Main program
print(f"=== Extraction of Polarsteps data ===")
# define json files names used by PS
trip_file = 'trip.json'
map_file = 'locations.json'
# analyse arguments given at launch
args_nb = len(sys.argv)
if args_nb > 0:
    args_index = 1
    while args_index <= args_nb-1:
        strParam = sys.argv[args_index]
        if strParam == "-email" or strParam == "-e": 
            mail = True
            args_index = args_index + 1
            if args_index <= args_nb-1:
                dest_email = sys.argv[args_index]
                print(f"Email option activated (sending to {dest_email}).")
            else:
                print(f"! Not enough arguments : missing destination email")
                printInstructions()
                exit()
        elif strParam == "-exclude" or strParam == "-x": 
            exclude = True 
            print(f"Exclude option activated.")
        elif strParam == "-interactive" or strParam == "-i": 
            interactive = True
            print(f"Interactive option activated.")            
        elif strParam == "-local" or strParam == "-l": 
            local = True
            print(f"Local html option activated.")
        elif strParam == "-v" or strParam == "-verbose":
            verbose = True
            print(f"Verbose option activated.")
        else: 
            print(f"! '{strParam}' is not an admitted parameter.")
            printInstructions()
            exit()
        args_index = args_index + 1
# create extraction directory to store all generated files
try:
    Path(extract_dir).mkdir(parents=True, exist_ok=True)
except:
    print(f"! Could not create directory ({extract_dir}) to host files.")
    exit()
# analyse locations file (just to generate a map with the tracks of the steps)
if os.path.exists(map_file):
    with open(map_file, encoding="utf-8" ) as f_in:
        print(f"Extracting trip track from {map_file} file...")
        loc_data = json.load(f_in)
        if gen_map: 
            trip_map = tile(staticmaps.tile_provider_ArcGISWorldImagery)
            #trip_map.set_zoom(9)
        sorted_by_time = sorted(loc_data['locations'], key=lambda x: x['time'])
        for loc in loc_data['locations']:
            #print("{\"lat\": "+str(loc['lat'])+", \"lon\": "+str(loc['lon'])+", \"time\": "+str(loc['time'])+"},")
            if gen_map: trip_map.add_object(staticmaps.Marker(staticmaps.create_latlng(loc['lat'], loc['lon']), size=2))     
        if gen_map and len(sorted_by_time)>0:
            if len(sorted_by_time)>1:
                line = [staticmaps.create_latlng(p['lat'], p['lon']) for p in sorted_by_time]
                trip_map.add_object(staticmaps.Line(line))
            trip_map_image = trip_map.render_cairo(800, 600)
            trip_map_image.write_to_png(f"{extract_dir}{os.sep}trip_map.png")
            print(f"Trip map generated.")
            no_location = False
else:
    print(f"! Locations file ({map_file}) not found.") 
# analyse trip file (with the most important informtion to extract)
if os.path.exists(trip_file):
    print(f"Extracting steps from {trip_file} file...")
    with open(trip_file, encoding="utf-8" ) as f_in:
        data = json.load(f_in)
    parse_data(data, os.getcwd(), extract_dir)
else:
    print(f"! Input file ({trip_file}) not found.")
    printInstructions()
