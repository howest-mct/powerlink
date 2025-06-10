from .Database import Database


class DataRepository:

    # region Read ---------------------------------

    @staticmethod
    def read_all_schedules():
        sql = """
            SELECT schedule_name, schedule_id, start_time, end_time, value, enabled
            FROM schedules s
        """
        return Database.get_rows(sql)

    def read_all_components():
        sql = """
            SELECT *
            FROM components c
        """
        return Database.get_rows(sql)

    def read_all_rooms():
        sql = """
            SELECT *
            FROM rooms
        """
        return Database.get_rows(sql)

    def read_all_components_in_frame(frame_id):
        sql = """
            SELECT * FROM components_frames WHERE frame_id = %s;
            """
        params = [frame_id]
        return Database.get_rows(sql, params)

    def add_component_to_frame(component_id, frame_id):
        sql = """
            INSERT INTO components_frames (component_id, frame_id) 
            VALUES (%s, %s);
            """
        params = [component_id, frame_id]
        return Database.execute_sql(sql, params)

    def remove_component_from_frame(component_id, frame_id):
        sql = """
            DELETE FROM components_frames 
            WHERE component_id = %s AND frame_id = %s;
            """
        params = [component_id, frame_id]
        return Database.execute_sql(sql, params)

    def check_component_in_frame_exists(component_id, frame_id):
        sql = """
            SELECT COUNT(*) as count FROM components_frames 
            WHERE component_id = %s AND frame_id = %s;
            """
        params = [component_id, frame_id]
        result = Database.get_one_row(sql, params)
        return result["count"] > 0 if result else False

    @staticmethod
    def read_last_log_by_id(log_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_name 
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE cl.log_id = %s
            ORDER BY cl.datetime DESC
            LIMIT 1
        """
        params = [log_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_all_last_logs(frame_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_id, r.room_name
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            JOIN components_frames sf ON cl.component_id = sf.component_id
            WHERE cl.datetime = (
                SELECT MAX(datetime)
                FROM component_logs cl2
                WHERE cl2.component_id = cl.component_id
            ) AND sf.frame_id = %s
            ORDER BY c.component_id;
        """
        params = [frame_id]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_all_schedules_by_frame_id(frame_id):
        sql = """
            SELECT s.*, r.room_name, t.type_name
            FROM schedules s
            JOIN schedules_frames sf ON s.schedule_id = sf.schedule_id
            JOIN rooms r ON s.room_id = r.room_id
            JOIN schedule_types t ON s.type_id = t.type_id
            WHERE sf.frame_id = %s;
        """
        params = [frame_id]
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

    @staticmethod
    def read_energy_24h(component_id):
        sql = """
            WITH ordered_logs AS (
                SELECT
                    component_id,
                    datetime,
                    value,
                    LEAD(datetime) OVER (PARTITION BY component_id ORDER BY datetime) AS next_datetime
                FROM component_logs
                WHERE component_id = %s
                AND DATE(datetime) = CURDATE()
            )
            SELECT 
                ROUND(SUM(value * TIMESTAMPDIFF(SECOND, datetime, next_datetime) / 3600), 2) AS total_kwh_today
            FROM ordered_logs
            WHERE next_datetime IS NOT NULL;
        """
        params = [component_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_energy_7d(component_id=2):
        sql = """
            WITH ordered_logs AS (
                SELECT
                    component_id,
                    datetime,
                    value,
                    LEAD(datetime) OVER (PARTITION BY component_id ORDER BY datetime) AS next_datetime
                FROM component_logs
                WHERE component_id = %s
                AND datetime >= CURDATE() - INTERVAL 7 DAY
            )
            SELECT 
                ROUND(SUM(value * TIMESTAMPDIFF(SECOND, datetime, next_datetime) / 3600), 2) AS total_kwh_week
            FROM ordered_logs
            WHERE next_datetime IS NOT NULL;
        """
        params = [component_id]
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

    @staticmethod
    def update_inverse_schedule(schedule_id, start_time, end_time, enabled):
        sql = "UPDATE schedules SET start_time = %s, end_time = %s, enabled = %s WHERE schedule_id = %s"
        params = [start_time, end_time, enabled, schedule_id]
        return Database.execute_sql(sql, params)

    # endregion Update ********************************
