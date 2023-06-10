from bs4 import BeautifulSoup
import datetime
import os
import requests
from Util import send_message

URL = "https://www.mensen.at/"
COOKIES = {"mensenExtLocation": "1"} # Set cookie for specific mensa entry (1 = JKU Linz Mensa)


def number_to_weekday(number : int) -> str:
    if number < 1 or number > 7:
        raise ValueError("Number must be between 1 and 7 but was " + str(number))

    weekdays = {
        1: "Montag",
        2: "Dienstag",
        3: "Mittwoch",
        4: "Donnerstag",
        5: "Freitag",
        6: "Samstag",
        7: "Sonntag"
    }

    return weekdays.get(number)




if __name__ == "__main__":
    # Get WebHook URL from environment variable
    WEBHOOK_URL = os.environ.get("DAILY_MENSA_WEBHOOK_URL")

    if WEBHOOK_URL is None:
        raise ValueError("Environment variable DAILY_MENSA_WEBHOOK_URL is not set")


    response = requests.get(URL, cookies=COOKIES, timeout=60)

    if response.status_code != 200:
        send_message(WEBHOOK_URL, "Error: " + str(response.status_code))
        exit(1)



    soup = BeautifulSoup(response.text, "html.parser")

    numericDay = datetime.datetime.today().weekday() + 1 # Monday = 1, …, Sunday = 7

    # Get menu-category
    menu_categories = soup.findAll("div", {"class": "menu-category"})
    # Remove the first (mobile version)
    menu_categories.pop(0)

    # Left (Menu 1 + Daily Plate)
    menu_category = menu_categories[0]
    # Get menu_item
    menu_items = menu_category.findAll("div", {"class": "menu-item-" + str(numericDay)})




    send_message(WEBHOOK_URL, "Mensa JKU Linz - " + number_to_weekday(numericDay))
