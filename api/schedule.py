from shedule.schedule import Schedule
from shedule.schedule_writer import ScheduleWriter


class ScheduleAPI:
    def __init__(self, db):
        self.db = db

    def get_by_profile_id(self, profile_id):
        schedule = Schedule()
        schedule.fetch_schedule(self.db, profile_id)
        schedule.build_schedule()
        # self.schedule.write_spreadsheet()
        schedule_writer = ScheduleWriter(schedule)
        schedule_writer.write_spreadsheet()

        return schedule
