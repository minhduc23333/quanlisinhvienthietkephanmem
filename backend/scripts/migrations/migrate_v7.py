"""Thêm thông tin giảng viên, học kỳ, giờ và phòng học, giữ dữ liệu cũ."""
from sqlalchemy import inspect,text
from app.core.database import engine
schema={'courses':{'lecturer':'VARCHAR(140) NULL','start_date':'VARCHAR(10) NULL','end_date':'VARCHAR(10) NULL'},
        'schedules':{'start_time':'VARCHAR(5) NULL','end_time':'VARCHAR(5) NULL','room':'VARCHAR(50) NULL'}}
with engine.begin() as conn:
    for table, fields in schema.items():
        if table not in inspect(conn).get_table_names():
            print(f'Chưa có bảng {table}; hãy tạo cơ sở dữ liệu trước.');continue
        existing={c['name'] for c in inspect(conn).get_columns(table)}
        for name,sqltype in fields.items():
            if name not in existing:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {sqltype}'))
                print('Đã thêm',table+'.'+name)
print('Migration V7 hoàn tất.')
