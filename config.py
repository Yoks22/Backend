import os
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote_plus

load_dotenv()


class Config:
    MYSQL_USER = os.getenv("MYSQL_USER") #, "vdi")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") #, "Qwerty123")
    MYSQL_HOST = os.getenv("MYSQL_HOST") #, "mysql-db")  # IMPORTANT: Docker service name
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DB = os.getenv("MYSQL_DB") #, "zoho_db")

    # URL encode credentials (MANDATORY for special chars)
    ENCODED_USER = quote_plus(MYSQL_USER)
    ENCODED_PASSWORD = quote_plus(MYSQL_PASSWORD)

    # SQLAlchemy connection string
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{ENCODED_USER}:{ENCODED_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Add your other Zoho configs below...
    # BASE_URL = ...
    # SYNC_INTERVAL_HOURS = ...

    # URL-encode the username and password to handle special characters
    ENCODED_USER = quote_plus(MYSQL_USER)
    ENCODED_PASSWORD = quote_plus(MYSQL_PASSWORD)

    # Zoho API Configuration
    CLIENT_ID = os.getenv('ZOHO_CLIENT_ID', '1000.GXPK7PLQD9SPH5G1MX6XB1Y3QBTXXN')
    CLIENT_SECRET = os.getenv('ZOHO_CLIENT_SECRET', '26832a9fc42886a569e9e41f5fce59d059375a3ae5')
    ACCESS_TOKEN = os.getenv('ZOHO_ACCESS_TOKEN',
                             '1000.9e59c7fd613af26575ae647baf7acf9f.5726a3090a451059ced5c1b0e0b9d9b6')
    REFRESH_TOKEN = os.getenv('ZOHO_REFRESH_TOKEN',
                              '1000.c133aa9661edd22553c3ee2bfb64572b.0f2497c83088b9d15edddd3cb91bd9cb')

    # Zoho India DC endpoints
    API_DOMAIN = os.getenv('ZOHO_API_DOMAIN', 'www.zohoapis.in')
    ACCOUNTS_DOMAIN = os.getenv('ZOHO_ACCOUNTS_DOMAIN', 'accounts.zoho.in')

    TOKEN_URL = f'https://{ACCOUNTS_DOMAIN}/oauth/v2/token'
    BASE_URL = f'https://{API_DOMAIN}/bigin/v2'

    # Sync Configuration
    MODULES_TO_FETCH = ["Contacts", "Accounts", "Pipelines", "Calls", "Events", "Tasks", "Notes"]
    RECORDS_PER_PAGE = int(os.getenv('RECORDS_PER_PAGE', '200'))
    RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '0.5'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    SYNC_INTERVAL_HOURS = int(os.getenv('SYNC_INTERVAL_HOURS', '168'))  # 168 hours = 1 week

    # Date range for queries
    MONTH_START = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    MONTH_END = datetime.now()
