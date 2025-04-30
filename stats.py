import sqlite3
from datetime import datetime, timedelta

def get_stats():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    now = datetime.now()

    last_hour = now - timedelta(hours=1)
    last_day = now - timedelta(days=1)
    last_week = now - timedelta(weeks=1)
    last_month = now - timedelta(days=30)

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp >= ?", (last_hour,))
    hour_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp >= ?", (last_day,))
    day_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp >= ?", (last_week,))
    week_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp >= ?", (last_month,))
    month_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    conn.close()
    return {
        'hour': hour_count,
        'day': day_count,
        'week': week_count,
        'month': month_count,
        'total': total_users
    }
