# PS_extract
Python script to extract PolarStep data from json files to txt file, local browsable html files or emails

## Introduction
If you use [PolarStep (PS)](https://www.polarsteps.com/) application to keep records of your journeys, you probably wanted to get your data back to be sure you have them outside the cloud, or to use them in other contexts. PS provides some [nice way to get all data and pictures from your account in a zip file](https://support.polarsteps.com/article/124-how-can-i-export-a-copy-of-my-data), but when you open it, it's really not convenient to handle the information stored in json files.
This script has been written to solve this and help you extracting all usefull information from these json files in an automatic way.
Furthermore it allows you to get the results in several formats:
- txt file describing all steps and listing pictures and videos associated
- local html files allowing to simply browse all the steps of your trip (with gallery of photos and videos and all information grabbed from PS)
- generated emails sent to a chosen address to populate automaticaly a blog

## Pre-requisites
[Python](https://www.python.org/) 3.6+ should be installed on your system.
This script needs also some libraries that should be installed prior to execution :
- [dateutil](https://github.com/dateutil/dateutil) : `pip install python-dateutil` or `python3 -m pip install --upgrade python-dateutil`
- [pillow](https://pypi.org/project/pillow/) : `pip install Pillow` or `python3 -m pip install --upgrade Pillow` ; this allows picture manipulations
- [pycairo](https://pypi.org/project/pycairo/) : `pip install pycairo` or `python3 -m pip install --upgrade pycairo` ; this allows anti-aliased maps
- [staticmaps](https://github.com/flopp/py-staticmaps) :
    - if you succesfully installed pycairo : `pip install py-staticmaps[cairo]` or `python3 -m pip install --upgrade py-staticmaps[cairo]`
    - if you did not installed pycairo : `pip install py-staticmaps` or `python3 -m pip install --upgrade py-staticmaps`

Also download your PS data and unzip it in a convenient place for you.

## Installation
You just need to copy the `extract.py` script at the root directory of the trip you want to extract.
(zip file provided by PS contains all your recorded trips in separated folders, each trip folder contains 2 files locations.json and trip.json and as many additionnal folders as the steps of your trip. Theses folders contain images and videos files related to each step)

## Execution
Run this program with the following command :

``python3 (/path_to_program_directory/)extract.py [options]``
    
The program will create an 'Extracts' directory and extract in it all informations from your PolarStep data in a readable text file (.txt), and some automatically generated static maps (PNG files) of your trip and steps.
In addition, you can ask to generate localy browsable HTML pages to navigate trough your steps, and/or generate emails for each steps (with text, images and videos from your steps). It is possible to extract data step by step in interactive mode, or to generate all files for the whole trip.

Here are the additional options that could be combined and put at launch:
+  ``-v``, ``-verbose`` :                  add additional information in generated text file
+ ``-l``, ``-local`` :                    to generale local html files to navigate the steps
+ ``-e``, ``-email address@domain.com`` : to send emails containing description, images and videos from extracted steps to the given address (to fill a blog for example, like blogger or wordpress using postie plugin ; consider to put your common email server parameters directly in the script)
+ ``-i``, ``-interactive`` :               to display analysis and ask interactively actions to be taken
+ ``-x``, ``-exclude`` :                  to exclude first and last steps from generated maps presenting the whole trip (allow to focus the map when origin country is distinct)
                           
anything else will display this help

## Contributions
First steps of extracting PS data were done through https://github.com/adamlporter/PolarSteps python script, giving me the basic elements to build this more featured script. 
