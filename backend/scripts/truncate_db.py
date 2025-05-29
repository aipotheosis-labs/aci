#!/usr/bin/env python3

from sqlalchemy import create_engine, text

from aci.server import config


def truncate_db() -> None:
    # Get the database URL
    db_url = config.DB_FULL_URL
    engine = create_engine(db_url)

    # Connect to database to truncate all tables
    with engine.connect() as conn:
        # Disable foreign key checks temporarily
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Get all table names
        result = conn.execute(
            text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'alembic_version'
        """)
        )
        tables = [row[0] for row in result]

        # Truncate all tables
        for table in tables:
            print(f"Truncating table: {table}")
            conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))

        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = 'origin';"))

        conn.commit()

    print("All tables have been truncated successfully!")


if __name__ == "__main__":
    truncate_db()
