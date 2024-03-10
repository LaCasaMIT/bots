# import MySQLdb as pymysql
import pymysql
import random


def make_teams():
    # connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", db="la_casa+site")
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM people WHERE resident=1""")
    rows = cursor.fetchall()
    residents_list = list(rows)

    cursor.execute("""SELECT id FROM chores_list ORDER BY id ASC""")
    rows = cursor.fetchall() # ((0,), (1,), (2,))  
    chores = []
    for row in rows:
        chores.append(row[0])

    for i in range(len(residents_list) // 2):
        # ('id', 'fname', 'lname', 'kerb', 'year', 'major', 'dietary_restriction', 'password', 'resident', 'onMealPlan')
        random_resident = random.choice(residents_list)
        kerb = random_resident[3]
        residents_list.remove(random_resident)

        cursor.execute("""INSERT into chores (kerb, team, chore, chores_completed) VALUES (%s, %s, %s, %s)""", (kerb, 1, chores[i], 0))

    for i, resident in enumerate(residents_list):
        kerb = resident[3]
        cursor.execute("""INSERT into chores (kerb, team, chore, chores_completed) VALUES (%s, %s, %s, %s)""", (kerb, 2, chores[i], 0))

    cursor.execute("""UPDATE chores_team SET team=%s""", (1,))

    connection.commit()
    connection.close()


def rotate_chores():
    # connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", db="la_casa+site")
    cursor = connection.cursor()

    cursor.execute("""SELECT active FROM chores_active""")
    active = cursor.fetchall()[0][0]

    if active == 1:
        cursor.execute("""SELECT team FROM chores_team""")
        team = cursor.fetchall()[0][0] # (("team_num",),)
        team = int(team)

        # cursor.execute("""SELECT chores.kerb, chores_list.id FROM chores LEFT JOIN chores_list ON chores.chore=chores_list.chore WHERE chores.team=%s ORDER BY id ASC""", (team,))
        cursor.execute("""SELECT chores.kerb, chores.chore, chores.team FROM chores WHERE chores.team=%s ORDER BY chore DESC""", (team,))
        rows = cursor.fetchall()

        # cursor.execute("""SELECT COUNT(*) FROM chores_list""")
        num_chores = 13 #cursor.fetchall()[0][0]

        for (kerb, chore_id, resident_team) in rows:     
            next_chore = (chore_id + 1)%num_chores
            if chore_id == 13 or chore_id == 14:
                next_chore = 0

            # if chore_id == 12:
            #     if resident_team == 1: 
            #         next_chore = 13
            #     elif resident_team == 2:
            #         next_chore = 14

            # cursor.execute("""SELECT chore FROM chores_list WHERE sort_order=%s""", (next_,))
            # new_chore = cursor.fetchall()[0][0]
            cursor.execute("""UPDATE chores SET chore=%s WHERE kerb=%s""", (next_chore, kerb,))
        
        if team == 1: new_team = 2
        else: new_team = 1
        cursor.execute("""UPDATE chores_team SET team=%s""", (new_team, ))

    connection.commit()
    connection.close()
        
if __name__ == "__main__":
    # to make and initiate random teams
    # TRUNCATE TABLE FIRST IN SQL DB
    # make_teams()

    # to rotate chores
    rotate_chores()
