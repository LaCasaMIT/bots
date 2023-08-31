import pymysql

class Resident:
    def __init__(self, kerb, onExec, room):
        self.kerb = kerb
        self.previous_pts = 0
        self.room_assignment_pts = 0
        self.chores_pts = 0
        self.rex_cpw_pts = 0
        self.retreat_attendance_pts = 0
        self.meeting_pts = 0
        self.total_housing_pts = 0
        self.onExec = onExec
        self.room = room
    
    def set_all_pts(self, cursor):
        self.total_housing_pts += \
            self.previous_pts + self.room_assignment_pts + \
            self.chores_pts + self.rex_cpw_pts + \
            self.retreat_attendance_pts + self.meeting_pts

        params = (self.previous_pts, self.room_assignment_pts, self.chores_pts, self.rex_cpw_pts, 
        self.retreat_attendance_pts, self.meeting_pts, self.total_housing_pts, self.kerb,)

        cursor.execute("""UPDATE housing_points SET previous_points=%s, room_assignment=%s, chores=%s, 
         REX_CPW=%s, retreat_attendance=%s, meeting_points=%s, total_housing_points=%s WHERE kerb=%s""", params)

def create_residents(cursor):
    cursor.execute("""SELECT people.kerb, resident_info.office, resident_info.room FROM people LEFT JOIN resident_info ON people.kerb=resident_info.kerb WHERE people.resident=1""")
    rows = cursor.fetchall()

    residents = []
    for kerb, position, room in rows:
        onExec = (position != "" and position != "Webmaster")
        resident = Resident(kerb, onExec, room)
        residents.append(resident)
    
    return residents

def create_dicts(cursor):
    cursor.execute("""SELECT kerb, total_housing_points FROM housing_points""")
    rows = cursor.fetchall()
    prev_pts = {kerb:pts for kerb, pts in rows}

    cursor.execute("""SELECT * FROM GBM_attendance""")
    rows = cursor.fetchall()
    gbm_attendance = {}
    retreat_attendance = {}
    REX_CPW = {}
    for kerb, status1, status2, status3, status4, retreat, rex_cpw in rows:
        gbm_attendance.update({kerb:[status1, status2, status3, status4]})
        retreat_attendance.update({kerb:retreat})
        REX_CPW.update({kerb:rex_cpw})

    cursor.execute("""SELECT * FROM EBM_attendance""")
    rows = cursor.fetchall()
    ebm_attendance = {kerb: [status1, status2, status3, status4] for kerb, status1, status2, status3, status4 in rows}
    
    cursor.execute("""SELECT * FROM rooms""")
    rows = cursor.fetchall()
    rooms = {room : Type for room, Type in rows}

    cursor.execute("""SELECT kerb, chores_completed FROM chores""")
    rows = cursor.fetchall()
    chores = {kerb : chores_completed for kerb, chores_completed in rows}

    return prev_pts, gbm_attendance, retreat_attendance, REX_CPW, ebm_attendance, rooms, chores

def calculate_points(residents, dicts, cursor):
    prev_pts, gbm_attendance, retreat_attendance, REX_CPW, ebm_attendance, rooms, chores = dicts

    for r in residents:
        #previous pts
        r.previous_pts = prev_pts[r.kerb]

        #rex/cpw pts
        if REX_CPW[r.kerb] == "absent":
            r.rex_cpw_pts = 0
        elif REX_CPW[r.kerb] == "present":
            r.rex_cpw_pts = .5

        #retreat pts
        if retreat_attendance[r.kerb] == "absent":
            r.retreat_attendance_pts = 0
        elif retreat_attendance[r.kerb] == "present":
            r.retreat_attendance_pts = .5
        
        #meeting pts
        meetings_attended = 0
        for attendance in gbm_attendance[r.kerb]:
            if attendance == "late":
                meetings_attended += .5
            elif attendance == "present":
                meetings_attended += 1

        cursor.execute("""SELECT * FROM GBM_dates WHERE dates!='0000-00-00'""")
        num_gbms = len(cursor.fetchall())

        cursor.execute("""SELECT * FROM EBM_dates WHERE dates!='0000-00-00'""")
        num_ebms = len(cursor.fetchall())

        if r.onExec:
            for attendance in ebm_attendance[r.kerb]: 
                if attendance == "late":
                    meetings_attended += .5
                elif attendance == "present":
                    meetings_attended += 1
            r.meeting_pts = (meetings_attended/(num_gbms + num_ebms))

        else: 
            r.meeting_pts = (meetings_attended/(num_gbms)) * .5

        #room assignment pts
        if rooms[r.room] == "SINGLE": r.room_assignment_pts = .5
        elif rooms[r.room] == "DOUBLE": r.room_assignment_pts = 1

        #chores pts
        # cursor.execute("SELECT total_chores FROM chores_total")
        # total_chores = cursor.fetchall()[0][0]
        r.chores_pts = chores[r.kerb] * .05

        # r.set_all_pts(cursor)

if __name__ == "__main__":
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    cursor = connection.cursor()

    dicts = create_dicts(cursor)
    residents = create_residents(cursor)
    calculate_points(residents, dicts, cursor)
        
    connection.commit()
    connection.close()
