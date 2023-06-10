import requests

def send_message(webhook:str, message:str) -> int:
    """Sends a message to a Discord Webhook

    Args:
        webhook (str): The Discord Webhook URL
        message (str): The message to send

    Returns:
        int: The HTTP status code of the request
    """
    data = {
        "content": message
    }

    response = requests.post(webhook, json=data, timeout=60)

    return response.status_code
