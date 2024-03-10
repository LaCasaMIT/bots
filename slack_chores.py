import logging
import os
# import MySQLdb as pymysql
import pymysql #works on computer
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def send_slack_reminder():
    slack_bot_token = "xoxb-281080591042-3691557209445-fLqYZqWGX5p3cDrpdjcfgvlv"
    channel_id = "C03LEG2BN3C"
    # channel_id = "C04BT71QW12" #test bots channel ID
    submit_chores_google_form = "https://docs.google.com/forms/d/e/1FAIpQLScbM03rAQHELUz1cHCh56fkp7Ks3GcqHEhHXj8rjToutX01KQ/viewform?usp=sf_link"
    chores_deadline = "Sunday at 1pm"
    # connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", db="la_casa+site")
    cursor = connection.cursor()

    cursor.execute("""SELECT active FROM chores_active""")
    active = cursor.fetchall()[0][0]

    if active == 1:
        cursor.execute("""SELECT team FROM chores_team""")
        team = cursor.fetchall()[0][0] # (("team_num",),)
        team = int(team)

        cursor.execute("""SELECT people.fname, people.lname, chores_list.chore FROM people LEFT JOIN chores ON people.kerb=chores.kerb LEFT JOIN chores_list ON chores.chore=chores_list.id WHERE chores.team=%s ORDER BY chores_list.id ASC""", (team,))
        rows = cursor.fetchall() # (('fname', 'chore'), ())
      
        text = "*TEAM " + str(team) + "* is up this week! Chores are due by *" + chores_deadline + ".* " + "Submit here: " + submit_chores_google_form + "\n\n"
        for fname, lname, chore in rows:
            text += fname + " " + lname + " - " + chore + "\n\n"
    else:
        text = "There are no chores this week!"

    connection.commit()
    connection.close()

    client = WebClient(token=os.environ.get(slack_bot_token))
    logger = logging.getLogger(__name__)

    try:
        result = client.chat_postMessage(
            token=slack_bot_token,
            channel=channel_id,
            text = "CHORES REMINDER! <!channel>",
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
        print("Error " + e)

if __name__ == "__main__":
    send_slack_reminder()
    pass