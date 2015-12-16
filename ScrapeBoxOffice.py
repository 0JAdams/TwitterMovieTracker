import urllib3
import re
from bs4 import BeautifulSoup
from collections import namedtuple
import arrow
import string
import time
import mysql.connector
from mysql.connector import errorcode


# create mySQL connection.  This needs connection info for the DB being used
try:
    cnx = mysql.connector.connect(user='', password='', host='', database='')
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("something is wrong with the SQL username or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

cursor = cnx.cursor()

# SQL statements to add box office and release date info into mySQL DB
add_boxofficenumbers = ("INSERT INTO boxoffice"
                        "(movie_name, date, dollarsearned)"
                        "VALUES (%s, %s, %s)")

update_releasedate = ("UPDATE movies "
                      "SET releaseDate=%s "
                      "WHERE movieName=%s")

movieURLDict = dict()
movieURLDict['Bridge of Spies'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=coldwar2015.htm'
movieURLDict['Crimson Peak'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=crimsonpeak.htm'
# movieURLDict['Every Thing Will Be Fine'] = ''
movieURLDict['Goosebumps'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=goosebumps.htm'
movieURLDict['Heist'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=heist2015.htm'
# movieURLDict['Lost in the Sun'] = ''
movieURLDict['Miss you Already'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=missyoualready.htm'
movieURLDict['My All American'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=myallamerican.htm'
movieURLDict['Pan'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=pan.htm'
movieURLDict['Sicario'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=sicario.htm'
movieURLDict['Spectre'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=bond24.htm'
movieURLDict['Star Wars Episode VII'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=starwars7.htm'
movieURLDict['Steve Jobs'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=jobs2015.htm'
movieURLDict['The Hallow'] = 'http://www.boxofficemojo.com/movies/?page=daily&id=thehallow.htm'
movieURLDict['The Hunger Games: Mockingjay - Part 2'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=hungergames4.htm'
movieURLDict['The Intern'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=intern.htm'
movieURLDict['The Last Witch Hunter'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=lastwitchhunter.htm'
movieURLDict['The Martian'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=scott2016.htm'
movieURLDict['Trumbo'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=trumbo2015.htm'
movieURLDict['Woodlawn'] = 'http://www.boxofficemojo.com/movies/?page=daily&view=chart&id=woodlawn.htm'

regex = re.compile('[%s]' % re.escape(string.punctuation))

# Get movie box office data
def getBoxOffice(movieToCheck, URLToCheck):
    http = urllib3.PoolManager()
    # headers = {'User-Agent': 'Mozilla/5.0'} #headers
    # req = http.request('GET', murl, None, headers)
    pageString = http.urlopen('GET', URLToCheck).data
    soup = BeautifulSoup(pageString, "html.parser")
    # print(soup.prettify())

    try:
        getReleaseDateFromSoup(soup, movieToCheck)
    except Exception as e:
        print("Error getting Release Date")
    table = soup.find("table", class_="chart-wide")
    # print(table.prettify())
    try:
        getBoxOfficeValuesFromTable(table, movieToCheck)
    except Exception as e :
        print("Error getting box office data")

def getReleaseDateFromSoup(soup, movieToCheck):
    table = soup.find("table", cellpadding="4", bgcolor="#dcdcdc", width="95%")
    # print(table.prettify())
    rows = table.find_all('tr')
    row0 = rows[0]
    row1 = rows[1]
    row0cols = row0.find_all('td')
    dateIn0 = False
    for col in row0cols:  # if the page doesn't have any boxoffice data yet, we need the release date from row 0, else row 1
        if "Release Date" in col.text:
            dateIn0 = True
    if dateIn0:
        row = row0
    else:
        row = row1
    cols = row.find_all('td')
    col = cols[1]  # we only want the col that has the release date
    release_date = col.b.nobr.a.text
    print(release_date)
    release_date_object = time.strptime(release_date, "%B %d, %Y")
    release_date_data = (release_date_object, movieToCheck)
    try:
        cursor.execute(update_releasedate, release_date_data)
        cnx.commit()
    except mysql.connector.Error as err:
        print("*** Something went wrong: {}".format(err))




def getBoxOfficeValuesFromTable(table, movieToCheck):
    rows = table.find_all('tr')  # get all rows
    for row in rows[1:]:  # skip the first row, which just has column names
        columns = row.find_all('td')  # get all row cells
        if len(columns) > 1:
            print(columns[1].b.text, ' -  ', columns[3].font.text)
            dateString = regex.sub('', columns[1].b.text)
            date_of_earnings = time.strptime(dateString, "%b %d %Y")
            print(date_of_earnings)
            numberString = regex.sub('', columns[3].font.text)
            print(numberString)
            movieData = (movieToCheck, date_of_earnings, numberString)
            try:
                cursor.execute(add_boxofficenumbers, movieData)
                cnx.commit()
            except mysql.connector.Error as err:
                print("*** Something went wrong: {}".format(err))



for movie in movieURLDict.keys():
    if movieURLDict[movie] is not '':
        movieNameToSearch = movie
        urlToSearch = movieURLDict[movie]
        getBoxOffice(movieNameToSearch, urlToSearch)

