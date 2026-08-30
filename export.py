import pandas as pd
import sqlite3

def export_to_excel():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('registrations.db')
        
        # Read the users table, excluding those who just clicked /start and never finished
        query = "SELECT id, telegram_id, full_name, phone, national_id, university, major, marital_status, status, ticket_code FROM users WHERE status != 'started'"
        df = pd.read_sql_query(query, conn)
        
        # Rename columns to Persian for a nice Excel output
        df = df.rename(columns={
            'id': 'شناسه دیتابیس',
            'telegram_id': 'آیدی عددی تلگرام',
            'full_name': 'نام و نام خانوادگی',
            'phone': 'شماره تماس',
            'national_id': 'کد ملی',
            'university': 'دانشگاه',
            'major': 'رشته تحصیلی',
            'marital_status': 'وضعیت تاهل',
            'status': 'وضعیت ثبت‌نام',
            'ticket_code': 'کد بلیط'
        })
        
        # Translate the status column
        status_translation = {
            'pending': 'در حال بررسی',
            'approved': 'تایید شده',
            'rejected': 'رد شده'
        }
        df['وضعیت ثبت‌نام'] = df['وضعیت ثبت‌نام'].map(status_translation).fillna(df['وضعیت ثبت‌نام'])
        
        # Export to Excel
        output_file = 'registrations.xlsx'
        df.to_excel(output_file, index=False)
        print(f"✅ Data exported successfully to {output_file}")
        
    except sqlite3.OperationalError:
        print("❌ Error: Could not find 'registrations.db'. Make sure the bot has been run and a user has registered.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    export_to_excel()
