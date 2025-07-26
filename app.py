import logging
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------
# Flask App Initialization
# ---------------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with your own secret key
app.secret_key = os.environ.get('SECRET_KEY', 'temporary_key_for_development')

# ---------------------------------------
# App Configuration (Inline)
# App Configuration
# ---------------------------------------
AWS_REGION_NAME = 'us-east-1'  # Mumbai region
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'ap-south-1')

# Email config
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'vajjalacharchitha@gmail.com'  # Your email
SENDER_PASSWORD = '1234'     # App password
ENABLE_EMAIL = True
# Email Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', 'False').lower() == 'true'

# SNS Topic ARN
app.config['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:897722694280:medin'
# Table Names from .env
USERS_TABLE_NAME = os.environ.get('USERS_TABLE_NAME', 'UsersTable')
APPOINTMENTS_TABLE_NAME = os.environ.get('APPOINTMENTS_TABLE_NAME', 'AppointmentsTable')

# SNS Configuration
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
ENABLE_SNS = os.environ.get('ENABLE_SNS', 'False').lower() == 'true'

# ---------------------------------------
# AWS Resources
# ---------------------------------------
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)
sns = boto3.client('sns', region_name=AWS_REGION_NAME)

# DynamoDB tables
# DynamoDB tables - update the table names to match exactly what's in your DynamoDB console
user_table = dynamodb.Table('UsersTable')  # Change to match your actual table name
appointment_table = dynamodb.Table('AppointmentsTable')  # Change to match your actual table name

# This function should match your table name exactly
def get_user_role(email):
    try:
        response = user_table.get_item(Key={'email': email})
        if 'Item' in response:
            return response['Item'].get('role')
    except Exception as e:
        app.logger.error(f"Error fetching role: {e}")
    return None

# Check if the table exists before trying to use it
def ensure_tables_exist():
    try:
        # List all tables in DynamoDB
        existing_tables = dynamodb.meta.client.list_tables()['TableNames']
        
        # Check if required tables exist
        if 'UsersTable' not in existing_tables:
            app.logger.error("UsersTable does not exist in DynamoDB")
            # You could create the table here if needed
            
        if 'AppointmentsTable' not in existing_tables:
            app.logger.error("AppointmentsTable does not exist in DynamoDB")
            # You could create the table here if needed
            
        return True
    except Exception as e:
        app.logger.error(f"Error checking tables: {e}")
        return False

# Call this function at app startup
ensure_tables_exist()
# DynamoDB Tables
user_table = dynamodb.Table(USERS_TABLE_NAME)
appointment_table = dynamodb.Table(APPOINTMENTS_TABLE_NAME)

def create_tables():
    # Check if tables exist first
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']
    
    # Create UsersTable if it doesn't exist
    if 'UsersTable' not in existing_tables:
        try:
            dynamodb.create_table(
                TableName='UsersTable',
                KeySchema=[
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'email',
                        'AttributeType': 'S'  # String
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Creating UsersTable. This may take a moment...")
            # Wait for table to be created
            dynamodb.meta.client.get_waiter('table_exists').wait(TableName='UsersTable')
            print("UsersTable created successfully!")
        except Exception as e:
            print(f"Error creating UsersTable: {e}")
    
    # Create AppointmentsTable if it doesn't exist
    if 'AppointmentsTable' not in existing_tables:
        try:
            dynamodb.create_table(
                TableName='AppointmentsTable',
                KeySchema=[
                    {
                        'AttributeName': 'appointment_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'appointment_id',
                        'AttributeType': 'S'  # String
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Creating AppointmentsTable. This may take a moment...")
            # Wait for table to be created
            dynamodb.meta.client.get_waiter('table_exists').wait(TableName='AppointmentsTable')
            print("AppointmentsTable created successfully!")
        except Exception as e:
            print(f"Error creating AppointmentsTable: {e}")
# ---------------------------------------
# Logging
# ---------------------------------------
logging.basicConfig(level=logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------------------------------
# Helper Functions
@@ -148,15 +71,14 @@ def is_logged_in():
def get_user_role(email):
try:
response = user_table.get_item(Key={'email': email})
        if 'Item' in response:
            return response['Item'].get('role')
        return response.get('Item', {}).get('role')
except Exception as e:
        app.logger.error(f"Error fetching role: {e}")
        logger.error(f"Error fetching role: {e}")
return None

def send_email(to_email, subject, body):
if not ENABLE_EMAIL:
        app.logger.info(f"[Email Skipped] Subject: {subject} to {to_email}")
        logger.info(f"[Email Skipped] Subject: {subject} to {to_email}")
return

try:
@@ -172,12 +94,31 @@ def send_email(to_email, subject, body):
server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
server.quit()

        app.logger.info(f"Email sent to {to_email}")
        logger.info(f"Email sent to {to_email}")
except Exception as e:
        app.logger.error(f"Email failed: {e}")
        logger.error(f"Email sending failed: {e}")

def publish_to_sns(message, subject="Salon Notification"):
    if not ENABLE_SNS:
        logger.info("[SNS Skipped] Message: {}".format(message))
        return

    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        logger.info(f"SNS published: {response['MessageId']}")
    except Exception as e:
        logger.error(f"SNS publish failed: {e}")

# -------------------------------
# Routes
# Routes (start here)
# -------------------------------

# Add your Flask routes here

# -------------------------------

# Home Page
@@ -237,7 +178,7 @@ def register():
user_table.put_item(Item=user_item)

# Send welcome email if enabled
        if app.config.get('ENABLE_EMAIL', False):
        if ENABLE_EMAIL:
welcome_msg = f"Welcome to HealthCare App, {name}! Your account has been created successfully."
send_email(email, "Welcome to HealthCare App", welcome_msg)

@@ -250,7 +191,7 @@ def register():
Subject='New User Registration - HealthCare App'
)
except Exception as e:
                app.logger.error(f"Failed to publish to SNS: {e}")
                logger.error(f"Failed to publish to SNS: {e}")

flash('Registration successful. Please log in.', 'success')
return redirect(url_for('login'))
@@ -290,7 +231,7 @@ def login():
ExpressionAttributeValues={':inc': 1, ':zero': 0}
)
except Exception as e:
                        app.logger.error(f"Failed to update login count: {e}")
                        logger.error(f"Failed to update login count: {e}")

flash('Login successful.', 'success')
return redirect(url_for('dashboard'))
@@ -323,39 +264,63 @@ def dashboard():
email = session['email']

if role == 'doctor':
        # Show doctor dashboard with list of appointments
        # Use GSI instead of scan for better performance
try:
            response = appointment_table.scan(
                FilterExpression="#doctor_email = :email",
                ExpressionAttributeNames={"#doctor_email": "doctor_email"},
            response = appointment_table.query(
                IndexName='DoctorEmailIndex',
                KeyConditionExpression="doctor_email = :email",
ExpressionAttributeValues={":email": email}
)
appointments = response['Items']
except Exception as e:
            app.logger.error(f"Failed to fetch appointments: {e}")
            appointments = []
            logger.error(f"Failed to fetch appointments: {e}")
            # Fallback to scan if GSI is not yet created
            try:
                response = appointment_table.scan(
                    FilterExpression="#doctor_email = :email",
                    ExpressionAttributeNames={"#doctor_email": "doctor_email"},
                    ExpressionAttributeValues={":email": email}
                )
                appointments = response['Items']
            except Exception as ex:
                logger.error(f"Fallback scan failed: {ex}")
                appointments = []
                
return render_template('doctor_dashboard.html', appointments=appointments)

elif role == 'patient':
        # Show patient dashboard with list of their appointments
        # Use GSI instead of scan for better performance
try:
            response = appointment_table.scan(
                FilterExpression="#patient_email = :email",
                ExpressionAttributeNames={"#patient_email": "patient_email"},
            response = appointment_table.query(
                IndexName='PatientEmailIndex',
                KeyConditionExpression="patient_email = :email",
ExpressionAttributeValues={":email": email}
)
appointments = response['Items']
            
            # Get list of doctors for booking new appointments
        except Exception as e:
            logger.error(f"Failed to query appointments: {e}")
            # Fallback to scan if GSI is not yet created
            try:
                response = appointment_table.scan(
                    FilterExpression="#patient_email = :email",
                    ExpressionAttributeNames={"#patient_email": "patient_email"},
                    ExpressionAttributeValues={":email": email}
                )
                appointments = response['Items']
            except Exception as ex:
                logger.error(f"Fallback scan failed: {ex}")
                appointments = []
                
        # Get list of doctors for booking new appointments
        try:
doctor_response = user_table.scan(
FilterExpression="#role = :role",
ExpressionAttributeNames={"#role": "role"},
ExpressionAttributeValues={":role": 'doctor'}
)
doctors = doctor_response['Items']
except Exception as e:
            app.logger.error(f"Failed to fetch data: {e}")
            appointments = []
            logger.error(f"Failed to fetch doctors: {e}")
doctors = []

return render_template('patient_dashboard.html', appointments=appointments, doctors=doctors)
@@ -403,7 +368,7 @@ def book_appointment():
appointment_table.put_item(Item=appointment_item)

# Send email notifications if enabled
            if app.config.get('ENABLE_EMAIL', False):
            if ENABLE_EMAIL:
# Send email notification to doctor
doctor_msg = f"Dear Dr. {doctor_name},\n\nA new appointment has been booked by {patient_name}.\n\nSymptoms: {symptoms}\nDate: {appointment_date}\n\nPlease login to your dashboard to view details."
send_email(doctor_email, "New Appointment Notification", doctor_msg)
@@ -412,10 +377,21 @@ def book_appointment():
patient_msg = f"Dear {patient_name},\n\nYour appointment with Dr. {doctor_name} has been booked successfully.\n\nDate: {appointment_date}\n\nThank you for using our healthcare service."
send_email(patient_email, "Appointment Confirmation", patient_msg)

            # Send SNS notification if configured
            if app.config.get('SNS_TOPIC_ARN'):
                try:
                    sns.publish(
                        TopicArn=app.config.get('SNS_TOPIC_ARN'),
                        Message=f'New appointment booked: Patient {patient_name} with Dr. {doctor_name} for date {appointment_date}',
                        Subject='New Appointment Booked - HealthCare App'
                    )
                except Exception as e:
                    logger.error(f"Failed to publish to SNS: {e}")
            
flash('Appointment booked successfully.', 'success')
return redirect(url_for('dashboard'))
except Exception as e:
            app.logger.error(f"Failed to book appointment: {e}")
            logger.error(f"Failed to book appointment: {e}")
flash('An error occurred while booking the appointment. Please try again.', 'danger')
return redirect(url_for('book_appointment'))

@@ -428,7 +404,7 @@ def book_appointment():
)
doctors = response['Items']
except Exception as e:
        app.logger.error(f"Failed to fetch doctors: {e}")
        logger.error(f"Failed to fetch doctors: {e}")
doctors = []
return render_template('book_appointment.html', doctors=doctors)

@@ -478,7 +454,7 @@ def view_appointment(appointment_id):
)

# Send email notification to patient if enabled
            if app.config.get('ENABLE_EMAIL', False):
            if ENABLE_EMAIL:
patient_email = appointment['patient_email']
patient_name = appointment.get('patient_name', 'Patient')
doctor_name = appointment.get('doctor_name', 'your doctor')
@@ -495,7 +471,7 @@ def view_appointment(appointment_id):
else:  # patient
return render_template('view_appointment_patient.html', appointment=appointment)
except Exception as e:
        app.logger.error(f"Error in view_appointment: {e}")
        logger.error(f"Error in view_appointment: {e}")
flash('An error occurred. Please try again.', 'danger')
return redirect(url_for('dashboard'))

@@ -541,7 +517,7 @@ def search_appointments():
appointments = response['Items']
return render_template('search_results.html', appointments=appointments, search_term=search_term)
except Exception as e:
            app.logger.error(f"Search failed: {e}")
            logger.error(f"Search failed: {e}")
flash('Search failed. Please try again.', 'danger')

return redirect(url_for('dashboard'))
@@ -590,7 +566,7 @@ def profile():

return render_template('profile.html', user=user)
except Exception as e:
        app.logger.error(f"Profile error: {e}")
        logger.error(f"Profile error: {e}")
flash('An error occurred. Please try again.', 'danger')
return redirect(url_for('dashboard'))

@@ -629,7 +605,7 @@ def submit_diagnosis(appointment_id):
)

# Send email notification to patient if enabled
        if app.config.get('ENABLE_EMAIL', False):
        if ENABLE_EMAIL:
patient_email = appointment['patient_email']
patient_name = appointment.get('patient_name', 'Patient')
doctor_name = session.get('name', 'your doctor')
@@ -640,13 +616,19 @@ def submit_diagnosis(appointment_id):
flash('Diagnosis submitted successfully.', 'success')
return redirect(url_for('dashboard'))
except Exception as e:
        app.logger.error(f"Submit diagnosis error: {e}")
        logger.error(f"Submit diagnosis error: {e}")
flash('An error occurred while submitting the diagnosis. Please try again.', 'danger')
return redirect(url_for('view_appointment', appointment_id=appointment_id))

# Health check endpoint for AWS load balancers
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

# -------------------------------
# Run the Flask app
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get port from environment or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
