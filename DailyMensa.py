import datetime
import os

import requests
from bs4 import BeautifulSoup

from Util import send_message

URL = "https://www.mensen.at/"
COOKIES = {"mensenExtLocation": "1"}  # Set cookie for specific mensa entry (1 = JKU Linz Mensa)

MESSAGE_TEMPLATE = """__***Mensa JKU Linz - {weekday}***__

**Menu Classic 1**
{menu_classic_1}

**Menu Classic 2**
{menu_classic_2}

**Tagesteller**
{daily_plate}"""


def number_to_weekday(number: int) -> str:
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

    numericDay = datetime.datetime.today().weekday() + 1  # Monday = 1, …, Sunday = 7

    message = ""
    if numericDay >= 6:
        numericDay = 1
        # TODO: Set it to the next Monday if it is Saturday or Sunday
        send_message(WEBHOOK_URL, "**The mensa is closed today.**")
        exit(0)

    # Left (Menu 1 + Daily Plate)
    menu_categories = soup.find("div", {"class": "menu-left"}).find("div", recursive=False)
    menu_items = menu_categories.find_all("div", {"class": "menu-item-" + str(numericDay)})
    menu_classic_1 = menu_items[0].text.strip()
    daily_plate = menu_items[1].text.strip()

    # Right (Menu 2) get item
    menu_categories = soup.find("div", {"class": "menu-right"}).find("div", recursive=False)
    menu_items = menu_categories.find("div", {"class": "menu-item-" + str(numericDay)})
    menu_classic_2 = menu_items.text.strip()

    # Send message
    message += MESSAGE_TEMPLATE.format(
        weekday=number_to_weekday(numericDay),
        menu_classic_1="> " + menu_classic_1.split("\n", 1)[1].replace("\n", "\n> "),
        menu_classic_2="> " + menu_classic_2.split("\n", 1)[1].replace("\n", "\n> "),
        daily_plate="> " + daily_plate.split("\n", 1)[1].replace("\n", "\n> ")
    )

    send_message(WEBHOOK_URL, message)
