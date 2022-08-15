import pymysql

class Resident:
    def __init__(self, fname, lname, kerb, year, onExec):
        self.fname = fname
        self.lname = lname
        self.kerb = kerb
        self.year = year
        self.previous_pts = 0
        self.room_assignment_pts = 0
        self.chores_pts = 0
        self.rex_cpw_pts = 0
        self.retreat_attendance_pts = 0
        self.meeting_pts = 0
        self.total_housing_pts = 0
        self.onExec = onExec
    
    def set_all_pts(self, cursor):
        self.total_housing_pts += \
            self.previous_pts + self.room_assignment_pts + \
            self.chores_pts + self.rex_cpw_pts + \
            self.retreat_attendance_pts + self.meeting_pts

        params = (self.previous_pts, self.room_assignment_pts, self.chores_pts, self.rex_cpw_pts, 
        self.retreat_attendance_pts, self.meeting_pts, self.total_housing_pts, self.kerb,)
        cursor.execute("""UPDATE housing_points SET previous_points=%s, room_assignment=%s, chores=%s, 
         REX_CPW=%s, retreat_attendance=%s, meeting_points=%s, TOTAL=%s WHERE kerb=%s""", params)


def create_residents(cursor):
    cursor.execute("""SELECT * FROM people""")
    rows = cursor.fetchall()

    residents = []
    for fname, lname, kerb, year, position, course in rows:
        onExec = position != ""
        resident = Resident(fname, lname, kerb, year, onExec)
        residents.append(resident)
    
    return residents

def create_dicts(cursor):
    cursor.execute("""SELECT kerb, TOTAL FROM housing_points""")
    rows = cursor.fetchall()
    prev_pts = {kerb:pts for kerb, pts in rows}

    cursor.execute("""SELECT * FROM GBM_attendance""")
    rows = cursor.fetchall()
    gbm_attendance = {}
    retreat_attendance = {}
    REX_CPW = {}
    for fname, lname, kerb, status1, status2, status3, status4, retreat, rex_cpw in rows:
        gbm_attendance.update({kerb:[status1, status2, status3, status4]})
        retreat_attendance.update({kerb:retreat})
        REX_CPW.update({kerb:rex_cpw})

    cursor.execute("""SELECT * FROM EBM_attendance""")
    rows = cursor.fetchall()
    ebm_attendance = {kerb: [status1, status2, status3, status4] for fname, lname, kerb, status1, status2, status3, status4 in rows}
    return prev_pts, gbm_attendance, retreat_attendance, REX_CPW, ebm_attendance

def calculate_points(residents, dicts, cursor):
    prev_pts, gbm_attendance, retreat_attendance, REX_CPW, ebm_attendance = dicts
    for r in residents:
        #previous pts
        r.previous_pts = prev_pts[r.kerb]

        #rex/cpw pts
        if REX_CPW[r.kerb] == "absent":
            r.rex_cpw_pts = 0
        else:
            r.rex_cpw_pts = .5

        #retreat pts
        if retreat_attendance[r.kerb] == "absent":
            r.retreat_attendance_pts = 0
        else:
            r.retreat_attendance_pts = .5
        
        #meeting pts
        meetings_attended = 0
        for attendance in gbm_attendance[r.kerb]:
            if attendance == "late":
                meetings_attended += .5
            elif attendance != "absent":
                meetings_attended += 1

        if r.onExec:
            for attendance in ebm_attendance[r.kerb]: 
                if attendance == "late":
                    meetings_attended += .5
                elif attendance != "absent":
                    meetings_attended += 1
            r.meeting_pts = (meetings_attended/8)

        else: 
            r.meeting_pts = (meetings_attended/4) * .5

        r.set_all_pts(cursor)

if __name__ == "__main__":
    connection = pymysql.connect(host="sql.mit.edu", user="la_casa", passwd="la_casa-webmaster", database="la_casa+site")
    cursor = connection.cursor()

    dicts = create_dicts(cursor)
    residents = create_residents(cursor)
    calculate_points(residents, dicts, cursor)
        
    connection.commit()
    connection.close()
