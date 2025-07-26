import logging
import os
import uuid
from dotenv import load_dotenv
from flask import Flask, session, render_template, request, redirect, url_for, flash
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from boto3.dynamodb.conditions import Key, Attr

# Load environment variables
load_dotenv()

# ---------------------------------------
# Flask App Initialization
# ---------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'temporary_key_for_development')

# ---------------------------------------
# App Configuration
# ---------------------------------------
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'us-east-1')

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', 'False').lower() == 'true'

app.config['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:897722694280:medin'
USERS_TABLE_NAME = os.environ.get('USERS_TABLE_NAME', 'UsersTable')
APPOINTMENTS_TABLE_NAME = os.environ.get('APPOINTMENTS_TABLE_NAME', 'AppointmentsTable')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
ENABLE_SNS = os.environ.get('ENABLE_SNS', 'False').lower() == 'true'

# ---------------------------------------
# AWS Resources
# ---------------------------------------
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)
sns = boto3.client('sns', region_name=AWS_REGION_NAME)

user_table = dynamodb.Table(USERS_TABLE_NAME)
appointment_table = dynamodb.Table(APPOINTMENTS_TABLE_NAME)

def get_user_role(email):
    try:
        response = user_table.get_item(Key={'email': email})
        return response.get('Item', {}).get('role')
    except Exception as e:
        logger.error(f"Error fetching role: {e}")
    return None

def ensure_tables_exist():
    try:
        existing_tables = dynamodb.meta.client.list_tables()['TableNames']
        if USERS_TABLE_NAME not in existing_tables:
            logger.error("UsersTable does not exist in DynamoDB")
        if APPOINTMENTS_TABLE_NAME not in existing_tables:
            logger.error("AppointmentsTable does not exist in DynamoDB")
        return True
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False

ensure_tables_exist()

def create_tables():
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']

    if USERS_TABLE_NAME not in existing_tables:
        try:
            dynamodb.create_table(
                TableName=USERS_TABLE_NAME,
                KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            dynamodb.meta.client.get_waiter('table_exists').wait(TableName=USERS_TABLE_NAME)
            print("UsersTable created successfully!")
        except Exception as e:
            print(f"Error creating UsersTable: {e}")

    if APPOINTMENTS_TABLE_NAME not in existing_tables:
        try:
            dynamodb.create_table(
                TableName=APPOINTMENTS_TABLE_NAME,
                KeySchema=[{'AttributeName': 'appointment_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'appointment_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            dynamodb.meta.client.get_waiter('table_exists').wait(TableName=APPOINTMENTS_TABLE_NAME)
            print("AppointmentsTable created successfully!")
        except Exception as e:
            print(f"Error creating AppointmentsTable: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ... (Your routes and views go here - already implemented in previous snippets)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
