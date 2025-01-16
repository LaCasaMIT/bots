from datetime import date
import logging
import os
# import MySQLdb as pymysql
import pymysql #works on computer
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def send_slack_reminder():
    slack_bot_token = "xoxb-281080591042-3827107045335-yELajiBDLrLQKYOxXrVoW2h5"

    channel_id = "C03LEG2BN3C"
    # channel_id = "C04BT71QW12" #test bots channel ID

    # connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", db="la_casa+site")
    cursor = connection.cursor()

    today = date.today().strftime("%Y-%m-%d")
    cursor.execute("""SELECT people.fname, people.lname, saves.request, people.dietary_restriction FROM saves LEFT JOIN people ON saves.kerb=people.kerb WHERE saves.day=%s""", (today,))
    saves = cursor.fetchall()

    connection.commit()
    connection.close()

    text_today = date.today().strftime("%m/%d")
    if saves:
        text = "*TODAY'S SAVES! - " + text_today + "*\n"
        text += "Any dietary restrictions are in *bold.*\n"
        if len(saves) == 1: 
            text += "There is *" + str(len(saves)) + "* save today:\n\n"
        else:
            text += "There are *" + str(len(saves)) + "* saves today:\n\n"
        for fname, lname, special_request, restriction in saves:
            text += fname + " " + lname
            if special_request and restriction:
                text += ' - ' + special_request + "; *" + restriction + "*"
            elif special_request:
                text += ' - ' + special_request
            elif restriction:
                text += " - *" + restriction + "*"
            text += "\n\n"

    else:
        text = "There are no saves for today."

    client = WebClient(token=os.environ.get(slack_bot_token))
    logger = logging.getLogger(__name__)

    try:
        result = client.chat_postMessage(
            token=slack_bot_token,
            channel=channel_id,
            text = "TODAY'S SAVES! <!channel>",
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }   
                }
            ]
        )

    except SlackApiError as e:
        print("Error " + str(e))

if __name__ == "__main__":
    send_slack_reminder()
    pass