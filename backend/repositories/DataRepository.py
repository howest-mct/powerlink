from .Database import Database
from datetime import datetime, timedelta


class DataRepository:

    # region Read ---------------------------------

    @staticmethod
    def read_log_by_id(log_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.log_id = %s
        """
        params = [log_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_all_logs():
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
        """
        return Database.get_rows(sql)

    @staticmethod
    def read_all_logs_by_component_id(component_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.component_id = %s
        """
        params = [component_id]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_last_log_by_component_id(component_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.component_id = %s 
            ORDER BY cl.datetime DESC 
            LIMIT 1
        """
        params = [component_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_all_last_logs(component_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            ORDER BY cl.datetime DESC 
            LIMIT 1
        """
        params = [component_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_logs_last_24_hours_by_component_id(component_id):
        one_day_ago = datetime.now() - timedelta(days=1)
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.component_id = %s AND cl.datetime >= %s
        """
        params = [component_id, one_day_ago]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_logs_last_week_by_component_id(component_id):
        one_week_ago = datetime.now() - timedelta(weeks=1)
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.component_id = %s AND cl.datetime >= %s
        """
        params = [component_id, one_week_ago]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_logs_between_1_and_2_weeks_by_component_id(component_id):
        one_week_ago = datetime.now() - timedelta(weeks=1)
        two_weeks_ago = datetime.now() - timedelta(weeks=2)
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.component_id = %s AND cl.datetime >= %s AND cl.datetime < %s
        """
        params = [component_id, two_weeks_ago, one_week_ago]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_all_schedules_by_frame_id(frame_name):
        sql = """
            SELECT s.*, r.room_name, t.type_name
            FROM schedules s
            JOIN schedules_frames sf ON s.schedule_id = sf.schedule_id
            JOIN frames f ON sf.frame_id = f.frame_id
            JOIN rooms r ON s.room_id = r.room_id
            JOIN schedule_types t ON s.type_id = t.type_id
            WHERE f.frame_name = %s;
        """
        params = [frame_name]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_schedule_by_id(schedule_id):
        sql = "SELECT * FROM schedules WHERE schedule_id = %s"
        params = [schedule_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_card_by_id(card_id):
        sql = "SELECT * FROM inhabitants WHERE card_id = %s"
        params = [card_id]
        return Database.get_one_row(sql, params)

    def read_inhabitant_by_card_id(card_id):
        sql = "SELECT * FROM inhabitants WHERE card_id = %s"
        params = [card_id]
        return Database.get_one_row(sql, params)

    # endregion Read ********************************

    # region Create ---------------------------------

    @staticmethod
    def create_log(value, component_id):
        sql = "INSERT INTO component_logs (value, component_id) VALUES (%s, %s)"
        params = [value, component_id]
        return Database.execute_sql(sql, params)

    # endregion Create ********************************

    # region Update ---------------------------------

    @staticmethod
    def update_schedule(schedule_id, start_time, end_time, value, enabled):
        sql = "UPDATE schedules SET start_time = %s, end_time = %s, value = %s, enabled = %s WHERE schedule_id = %s"
        params = [start_time, end_time, value, enabled, schedule_id]
        return Database.execute_sql(sql, params)

    # endregion Update ********************************
