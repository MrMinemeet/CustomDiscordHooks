import datetime
from os import path
import sys
import requests
from bs4 import BeautifulSoup
from Util import send_message


def number_to_weekday(number: int) -> str:
    """
    Converts a number to a weekday
    Args:
        number: A number between 1 and 7
    Returns: The weekday as a string
    """

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

def load_webhooks() -> list[str]:
    """
    Loads the webhooks from the webhook file
    Returns: A list of webhooks
    """
    try:
        webhook_path = path.join(path.dirname(path.abspath(__file__)), "mensen_webhooks.txt")
        with open(webhook_path, "r", encoding='utf-8') as f:
            lines = f.readlines()
            return [line.strip() for line in lines]
    except FileNotFoundError:
        print("Error: Could not open webhook file")
        sys.exit(2)

def get_jku_mensa(numericDay: int) -> str:
    """
    Gets the menu for the JKU Mensa
    Returns: A string containing the menu
    """

    MESSAGE_TEMPLATE = """__***JKU Linz Mensa - {weekday}***__

    **Menu Classic 1**
    {menu_classic_1}

    **Menu Classic 2**
    {menu_classic_2}

    **Tagesteller**
    {daily_plate}"""

    URL = "https://www.mensen.at/"
    COOKIES = {"mensenExtLocation": "1"}  # Set cookie for specific mensa entry (1 = JKU Linz Mensa)

    response = requests.get(URL, cookies=COOKIES, timeout=60)

    if response.status_code != 200:
        print("Error: Could not load mensa page. Status code: " + str(response.status_code))
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")


    # Left (Menu 1 + Daily Plate)
    menu_categories = soup.find("div", {"class": "menu-left"}).find("div", recursive=False)
    menu_items = menu_categories.find_all("div", {"class": "menu-item-" + str(numericDay)})
    menu_classic_1 = str(menu_items[0].text.strip())
    daily_plate = str(menu_items[1].text.strip())
    menu_classic_1 = menu_classic_1.split("\n", 1)

    if len(menu_classic_1) == 2:
        menu_classic_1 = menu_classic_1[1]
    else:
        menu_classic_1 = "Kein Menü 1"

    daily_plate = daily_plate.split("\n", 1)[1]

    if len(daily_plate) == 0:
        daily_plate = "Kein Tagesteller"
    else:
        split_daily_plates = daily_plate.split("\nTagesgericht")

        if len(split_daily_plates) > 1:
            split_daily_plates[1] = f"Tagesgericht {split_daily_plates[1]}"

        daily_plate = ""
        for split in split_daily_plates:
            plate_split = split.split("\n", 1)
            daily_plate += f"**{plate_split[0].strip()}**\n{plate_split[1].replace("\n", " ").strip()}\n"
            



    # Right (Menu 2) get item
    menu_categories = soup.find("div", {"class": "menu-right"}).find("div", recursive=False)
    menu_items = menu_categories.find("div", {"class": "menu-item-" + str(numericDay)})
    menu_classic_2 = str(menu_items.text.strip())
    menu_classic_2 = menu_classic_2.split("\n", 1)

    if len(menu_classic_2) == 2:
        menu_classic_2 = menu_classic_2[1]
    else:
        menu_classic_2 = "Kein Menü 2"
    

    # Send message
    return MESSAGE_TEMPLATE.format(
        weekday=number_to_weekday(numericDay),
        menu_classic_1="> " + menu_classic_1.replace("\n", "\n> "),
        menu_classic_2="> " + menu_classic_2.replace("\n", "\n> "),
        daily_plate="> " + daily_plate.strip().replace("\n", "\n> ")
    )

def get_raab_mensa(numericDay: int) -> str:
    """
    Gets the menu for the Raab Mensa
    Returns: A string containing the menu
    """

    MESSAGE_TEMPLATE = """__***Raab Mensa - {weekday}***__

    **MENU 1**
    {menu_1}

    **MENU 2**
    {menu_2}
    """

    URL = "https://www.mittag.at/r/raabmensa"

    response = requests.get(URL, timeout=60)

    if response.status_code != 200:
        print("Error: Could not load mensa page. Status code: " + str(response.status_code))
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    menus = soup.find("div", {"class": "current-menu"})

    msg = ""

    for e in menus:
        e = str(e)
        if "<br/>" in e:
            msg += "\n"
        else:
            msg += e

    msg = msg.replace("\n\n", "\n").split("MENÜ 1",1)[1].split("MENÜ 2")
    if len(msg[0].strip()) == 0:
        msg[0] = "Kein Menü 1"
    if len(msg[1].strip()) == 0:
        msg[1] = "Kein Menü 2"

    menu1 = msg[0].strip().replace("\n", "\n> ").strip()
    menu2 = msg[1].strip().replace("\n", "\n> ").strip()

    # Send message
    return MESSAGE_TEMPLATE.format(
        weekday=number_to_weekday(numericDay),
        menu_1="> " + menu1,
        menu_2="> " + menu2
    )

if __name__ == "__main__":
    NUMERIC_DAY = datetime.datetime.today().weekday() + 1  # Monday = 1, …, Sunday = 7
    if NUMERIC_DAY >= 6:
        NUMERIC_DAY = 1
        # TODO: Set it to the next Monday if it is Saturday or Sunday
        sys.exit(0)

    message = ""

    try:
        message += get_jku_mensa(NUMERIC_DAY)
    except Exception as e:
        print(f"Failed to get information from JKU Mensa: {str(e)}")

    message += "\n\n"

    try:
        message += get_raab_mensa(NUMERIC_DAY)
    except Exception as e:
        print(f"Failed to get information Raab Mensa: {str(e)}")


    for webhook in load_webhooks():
        send_message(webhook, message)
