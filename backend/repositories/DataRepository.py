import mysql
from .Database import Database
import pandas as pd
from datetime import datetime, timedelta


class DataRepository:

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

    def read_all_components_in_page(page_id):
        sql = """
            SELECT * FROM components_pages WHERE page_id = %s;
            """
        params = [page_id]
        result = Database.get_rows(sql, params)

        if not result:
            return []
        return result

    def add_component_to_page(component_id, page_id):
        sql = """
            INSERT INTO components_pages (component_id, page_id) 
            VALUES (%s, %s);
            """
        params = [component_id, page_id]
        return Database.execute_sql(sql, params)

    def remove_component_from_page(component_id, page_id):
        sql = """
            DELETE FROM components_pages 
            WHERE component_id = %s AND page_id = %s;
            """
        params = [component_id, page_id]
        return Database.execute_sql(sql, params)

    def check_component_in_page_exists(component_id, page_id):
        sql = """
            SELECT COUNT(*) as count FROM components_pages
            WHERE component_id = %s AND page_id = %s;
            """
        params = [component_id, page_id]
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
    def read_all_last_logs(page_id):
        sql = """
            SELECT cl.*, c.component_name, c.value_unit, r.room_id, r.room_name
            FROM component_logs cl
            JOIN components c ON cl.component_id = c.component_id
            JOIN rooms r ON c.room_id = r.room_id
            JOIN components_pages sf ON cl.component_id = sf.component_id
            WHERE cl.datetime = (
                SELECT MAX(datetime)
                FROM component_logs cl2
                WHERE cl2.component_id = cl.component_id
            ) AND sf.page_id = %s
            ORDER BY c.component_id;
        """
        params = [page_id]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_all_schedules_by_page_id(page_id):
        sql = """
            SELECT s.*, r.room_name, t.type_name
            FROM schedules s
            JOIN schedules_pages sf ON s.schedule_id = sf.schedule_id
            JOIN rooms r ON s.room_id = r.room_id
            JOIN schedule_types t ON s.type_id = t.type_id
            WHERE sf.page_id = %s;
        """
        params = [page_id]
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
                ROUND(SUM(value * TIMESTAMPDIFF(SECOND, datetime, next_datetime) / 3600), 2) AS total_kwh
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
                ROUND(SUM(value * TIMESTAMPDIFF(SECOND, datetime, next_datetime) / 3600), 2) AS total_kwh
            FROM ordered_logs
            WHERE next_datetime IS NOT NULL;
        """
        params = [component_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_log_history_24h(component_id):
        sql = """
            SELECT datetime, value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY datetime;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            empty_result = []

            for hour_number in range(24):
                hours_ago = 23 - hour_number
                time_for_this_hour = current_hour - timedelta(hours=hours_ago)

                empty_result.append(
                    {
                        "chart_date": time_for_this_hour.strftime("%Y-%m-%d %H:00:00"),
                        "average_value": 0.0,
                    }
                )

            return empty_result

        df = pd.DataFrame(raw_data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        df = df.sort_values("datetime")
        df["wh_consumed"] = 0.0

        for i in range(1, len(df)):
            time_diff = (
                df.iloc[i]["datetime"] - df.iloc[i - 1]["datetime"]
            ).total_seconds() / 3600
            wh = df.iloc[i - 1]["value"] * time_diff
            df.iloc[i, df.columns.get_loc("wh_consumed")] = wh

        df["hour_slot"] = df["datetime"].dt.floor("H")
        hourly_wh = df.groupby("hour_slot")["wh_consumed"].sum()

        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        first_hour = current_hour - timedelta(hours=23)
        all_hours_we_want = pd.date_range(start=first_hour, end=current_hour, freq="H")

        complete_data = hourly_wh.reindex(all_hours_we_want, fill_value=0)

        final_result = []
        for hour_timestamp, total_wh in complete_data.items():
            final_result.append(
                {
                    "chart_date": hour_timestamp.strftime("%Y-%m-%d %H:00:00"),
                    "average_value": round(float(total_wh), 2),
                }
            )

        return final_result

    @staticmethod
    def read_log_history_7d(component_id):
        sql = """
            SELECT datetime, value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY datetime;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            today = datetime.now().date()
            empty_result = []

            for day_number in range(7):
                days_ago = 6 - day_number
                date_for_this_day = today - timedelta(days=days_ago)

                empty_result.append(
                    {
                        "chart_date": date_for_this_day.strftime("%Y-%m-%d"),
                        "average_value": 0.0,
                    }
                )

            return empty_result

        df = pd.DataFrame(raw_data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        df = df.sort_values("datetime")
        df["wh_consumed"] = 0.0

        for i in range(1, len(df)):
            time_diff = (
                df.iloc[i]["datetime"] - df.iloc[i - 1]["datetime"]
            ).total_seconds() / 3600
            wh = df.iloc[i - 1]["value"] * time_diff
            df.iloc[i, df.columns.get_loc("wh_consumed")] = wh

        df["day_slot"] = df["datetime"].dt.date
        daily_wh = df.groupby("day_slot")["wh_consumed"].sum()

        today = datetime.now().date()
        first_day = today - timedelta(days=6)

        all_days_we_want = pd.date_range(start=first_day, end=today, freq="D").date

        daily_wh.index = pd.to_datetime(daily_wh.index).date

        final_result = []
        for day_date in all_days_we_want:
            total_wh = daily_wh.get(day_date, 0.0)
            final_result.append(
                {
                    "chart_date": day_date.strftime("%Y-%m-%d"),
                    "average_value": round(float(total_wh), 2),
                }
            )

        return final_result

    @staticmethod
    def read_log_history_14d(component_id):
        sql = """
            SELECT datetime, value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            ORDER BY datetime;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            today = datetime.now().date()
            empty_result = []

            for day_number in range(14):
                days_ago = 13 - day_number
                date_for_this_day = today - timedelta(days=days_ago)

                empty_result.append(
                    {
                        "chart_date": date_for_this_day.strftime("%Y-%m-%d"),
                        "average_value": 0.0,
                    }
                )

            return empty_result

        df = pd.DataFrame(raw_data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        df = df.sort_values("datetime")
        df["wh_consumed"] = 0.0

        for i in range(1, len(df)):
            time_diff = (
                df.iloc[i]["datetime"] - df.iloc[i - 1]["datetime"]
            ).total_seconds() / 3600
            wh = df.iloc[i - 1]["value"] * time_diff
            df.iloc[i, df.columns.get_loc("wh_consumed")] = wh

        df["day_slot"] = df["datetime"].dt.date
        daily_wh = df.groupby("day_slot")["wh_consumed"].sum()

        today = datetime.now().date()
        first_day = today - timedelta(days=13)

        all_days_we_want = pd.date_range(start=first_day, end=today, freq="D").date

        daily_wh.index = pd.to_datetime(daily_wh.index).date

        final_result = []
        for day_date in all_days_we_want:
            total_wh = daily_wh.get(day_date, 0.0)
            final_result.append(
                {
                    "chart_date": day_date.strftime("%Y-%m-%d"),
                    "average_value": round(float(total_wh), 2),
                }
            )

        return final_result

    @staticmethod
    def read_temp_history_14d(component_id):
        sql = """
            SELECT datetime, value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            ORDER BY datetime;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            today = datetime.now().date()
            empty_result = []

            for day_number in range(14):
                days_ago = 13 - day_number
                date_for_this_day = today - timedelta(days=days_ago)

                empty_result.append(
                    {
                        "chart_date": date_for_this_day.strftime("%Y-%m-%d"),
                        "average_value": 0.0,
                    }
                )

            return empty_result

        df = pd.DataFrame(raw_data)
        df["datetime"] = pd.to_datetime(df["datetime"])

        df = df.sort_values("datetime")
        df["wh_consumed"] = 0.0

        for i in range(1, len(df)):
            time_diff = (
                df.iloc[i]["datetime"] - df.iloc[i - 1]["datetime"]
            ).total_seconds() / 3600
            wh = df.iloc[i - 1]["value"] * time_diff
            df.iloc[i, df.columns.get_loc("wh_consumed")] = wh

        df["day_slot"] = df["datetime"].dt.date
        daily_wh = df.groupby("day_slot")["wh_consumed"].sum()

        today = datetime.now().date()
        first_day = today - timedelta(days=13)

        all_days_we_want = pd.date_range(start=first_day, end=today, freq="D").date

        daily_wh.index = pd.to_datetime(daily_wh.index).date

        final_result = []
        for day_date in all_days_we_want:
            total_wh = daily_wh.get(day_date, 0.0)
            final_result.append(
                {
                    "chart_date": day_date.strftime("%Y-%m-%d"),
                    "average_value": round(float(total_wh), 2),
                }
            )

        return final_result

    @staticmethod
    def read_log_history_15min(component_id):
        sql = """
            SELECT 
                DATE_FORMAT(datetime, '%Y-%m-%d %H:%i:00') as minute_part,
                AVG(value) as average_value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
            GROUP BY DATE_FORMAT(datetime, '%Y-%m-%d %H:%i:00')
            ORDER BY minute_part;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            now = datetime.now()
            empty_result = []
            for minute_offset in range(15):
                time_for_minute = now - timedelta(minutes=14 - minute_offset)
                minute_rounded = time_for_minute.replace(second=0, microsecond=0)
                empty_result.append(
                    {
                        "chart_date": minute_rounded.strftime("%Y-%m-%d %H:%M:%S"),
                        "average_value": 0.0,
                    }
                )
            return empty_result

        data_lookup = {}
        for row in raw_data:
            minute_key = str(row["minute_part"])
            data_lookup[minute_key] = round(float(row["average_value"]), 2)

        result = []
        now = datetime.now()
        for minute_offset in range(15):
            time_for_minute = now - timedelta(minutes=14 - minute_offset)
            minute_rounded = time_for_minute.replace(second=0, microsecond=0)
            minute_str = minute_rounded.strftime("%Y-%m-%d %H:%M:00")
            avg_value = data_lookup.get(minute_str, 0.0)

            result.append(
                {
                    "chart_date": minute_rounded.strftime("%Y-%m-%d %H:%M:%S"),
                    "average_value": avg_value,
                }
            )

        return result

    @staticmethod
    def read_temperature_daily_history_7d(component_id):
        sql = """
            SELECT 
                DATE(datetime) as date_part,
                AVG(value) as average_value
            FROM component_logs 
            WHERE component_id = %s
                AND datetime >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(datetime)
            ORDER BY date_part;
        """
        raw_data = Database.get_rows(sql, [component_id])

        if not raw_data:
            today = datetime.now().date()
            empty_result = []
            for day_offset in range(7):
                date_for_day = today - timedelta(days=6 - day_offset)
                empty_result.append(
                    {
                        "chart_date": date_for_day.strftime("%Y-%m-%d"),
                        "average_value": 0.0,
                    }
                )
            return empty_result

        data_lookup = {}
        for row in raw_data:
            date_key = str(row["date_part"])
            data_lookup[date_key] = round(float(row["average_value"]), 2)

        result = []
        today = datetime.now().date()
        for day_offset in range(7):
            date_for_day = today - timedelta(days=6 - day_offset)
            date_str = str(date_for_day)
            avg_value = data_lookup.get(date_str, 0.0)

            result.append(
                {
                    "chart_date": date_for_day.strftime("%Y-%m-%d"),
                    "average_value": avg_value,
                }
            )

        return result

    @staticmethod
    def read_log_count_history_7d_by_id(component_id):
        sql = """
            SELECT 
                component_id,
                DATE(datetime) as chart_date,
                COUNT(*) as log_count
            FROM component_logs 
            WHERE component_id = %s 
            AND datetime >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY component_id, DATE(datetime)
            ORDER BY chart_date ASC;
        """
        params = [component_id]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_last_entered(card_id):
        sql = """
            SELECT i.first_name
            FROM component_logs cl
            LEFT JOIN inhabitants i 
            ON CAST(cl.value AS CHAR) = CAST(i.card_id AS CHAR)
            WHERE CAST(cl.value AS CHAR) = %s
            ORDER BY cl.datetime DESC
            LIMIT 1;
        """
        params = [str(card_id)]
        result = Database.get_one_row(sql, params)

        if result:
            return result
        return "Unknown"

    @staticmethod
    def create_log(value, component_id):
        sql = "INSERT INTO component_logs (value, component_id) VALUES (%s, %s)"
        params = [value, component_id]
        return Database.execute_sql(sql, params)

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
