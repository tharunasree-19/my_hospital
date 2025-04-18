from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bcrypt import hashpw, gensalt, checkpw
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Add context processor for datetime
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  # Update to your AWS region

# DynamoDB Tables
users_table = dynamodb.Table('NextGenHospital_Users')
doctors_table = dynamodb.Table('NextGenHospital_Doctors')
appointments_table = dynamodb.Table('NextGenHospital_Appointments')
patient_records_table = dynamodb.Table('NextGenHospital_PatientRecords')
contact_messages_table = dynamodb.Table('NextGenHospital_ContactMessages')

# Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "gtharunasri19@gmail.com"  # Update with your email
SENDER_PASSWORD = "umpb bimb pahp axmc"  # Update with your app password

# Health tips data
health_tips = [
    {
        "title": "Stay Hydrated",
        "content": "Drink at least 8 glasses of water daily to maintain proper bodily functions and energy levels.",
        "category": "General"
    },
    {
        "title": "Regular Exercise",
        "content": "Aim for at least 30 minutes of moderate exercise most days of the week.",
        "category": "Fitness"
    },
    {
        "title": "Balanced Diet",
        "content": "Include fruits, vegetables, whole grains, lean proteins, and healthy fats in your daily meals.",
        "category": "Nutrition"
    },
    {
        "title": "Cold Relief",
        "content": "For common cold symptoms, rest, stay hydrated, and try honey with warm water and lemon.",
        "category": "Home Remedy"
    },
    {
        "title": "Headache Management",
        "content": "For tension headaches, try applying a cold or warm compress to your head for 5-10 minutes.",
        "category": "Pain Management"
    },
    {
        "title": "Proper Sleep",
        "content": "Aim for 7-9 hours of quality sleep each night to support overall health.",
        "category": "Wellness"
    }
]

# Common ailments and basic advice
common_ailments = {
    "cold": {
        "symptoms": "Runny nose, sneezing, sore throat, cough",
        "remedy": "Rest, stay hydrated, use a humidifier, gargle with salt water for sore throat",
        "when_to_see_doctor": "If symptoms persist beyond 10 days or are severe"
    },
    "fever": {
        "symptoms": "Elevated body temperature, chills, headache, muscle aches",
        "remedy": "Rest, stay hydrated, take acetaminophen or ibuprofen as directed",
        "when_to_see_doctor": "If fever exceeds 103°F (39.4°C) or lasts more than 3 days"
    },
    "headache": {
        "symptoms": "Pain or discomfort in the head, scalp, or neck",
        "remedy": "Rest in a dark quiet room, apply cold or warm compress, stay hydrated",
        "when_to_see_doctor": "If headache is severe, sudden, or accompanied by other symptoms"
    },
    "upset_stomach": {
        "symptoms": "Nausea, vomiting, diarrhea, abdominal pain",
        "remedy": "Clear liquids, BRAT diet (bananas, rice, applesauce, toast), avoid dairy and fatty foods",
        "when_to_see_doctor": "If symptoms are severe or last more than 2 days"
    }
}

# Function to send email
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Helper function to check if user is logged in
def is_logged_in():
    return 'user_email' in session

# Home route
@app.route('/')
def home():
    # Get random health tips to display on homepage
    random_tips = random.sample(health_tips, min(3, len(health_tips)))
    return render_template('index.html', tips=random_tips, is_logged_in=is_logged_in())

# Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form['phone']
        
        # Basic Validation
        if not name or not email or not password or not confirm_password or not phone:
            flash("All fields are mandatory! Please fill out the entire form.", "danger")
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash("Passwords do not match! Please try again.", "danger")
            return redirect(url_for('register'))

        # Check if user already exists
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            flash("User already exists! Please log in.", "info")
            return redirect(url_for('login'))

        # Hash the password
        hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

        # Store user in DynamoDB
        users_table.put_item(
            Item={
                'email': email,
                'name': name,
                'password': hashed_password,
                'phone': phone,
                'user_type': 'patient',  # Default role is patient
                'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create an empty patient record
        patient_records_table.put_item(
            Item={
                'patient_id': email,
                'name': name,
                'email': email,
                'phone': phone,
                'medical_history': [],
                'allergies': [],
                'medications': [],
                'blood_type': '',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Send welcome email
        welcome_message = f"Welcome to Next Gen Hospital, {name}!\n\nThank you for registering with us. We're dedicated to providing you with the best healthcare services."
        send_email(email, "Welcome to Next Gen Hospital", welcome_message)
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html', is_logged_in=is_logged_in())

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Basic Validation
        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return redirect(url_for('login'))

        # Fetch user data from DynamoDB
        response = users_table.get_item(Key={'email': email})
        user = response.get('Item')

        if not user or not checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            flash("Incorrect email or password! Please try again.", "danger")
            return redirect(url_for('login'))

        # Store user info in session
        session['user_email'] = email
        session['user_name'] = user['name']
        session['user_type'] = user['user_type']
        
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for('home'))
        
    return render_template('login.html', is_logged_in=is_logged_in())

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))

# About Page
@app.route('/about')
def about():
    return render_template('about.html', is_logged_in=is_logged_in())

# Contact Page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        # Store message in DynamoDB
        contact_messages_table.put_item(
            Item={
                'message_id': str(uuid.uuid4()),
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
                'submitted_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'new'
            }
        )
        
        # Send confirmation email
        confirmation_message = f"Dear {name},\n\nThank you for contacting Next Gen Hospital. We have received your message and will get back to you soon.\n\nBest regards,\nNext Gen Hospital Team"
        send_email(email, "Thank you for contacting Next Gen Hospital", confirmation_message)
        
        # Send notification to hospital staff
        admin_message = f"New contact message from {name} ({email})\nSubject: {subject}\n\nMessage:\n{message}"
        send_email(SENDER_EMAIL, f"New Contact Form Submission: {subject}", admin_message)
        
        flash("Your message has been sent! We'll get back to you soon.", "success")
        return redirect(url_for('contact'))
        
    return render_template('contact.html', is_logged_in=is_logged_in())

# Doctors List Page
@app.route('/doctors')
def doctors_list():
    # Get all doctors from DynamoDB
    response = doctors_table.scan()
    doctors = response.get('Items', [])
    
    # Sort doctors by specialty for better organization
    doctors.sort(key=lambda x: x.get('specialty', ''))
    
    return render_template('doctors.html', doctors=doctors, is_logged_in=is_logged_in())

# Doctor Details Page
@app.route('/doctor/<doctor_id>')
def doctor_details(doctor_id):
    # Get doctor details from DynamoDB
    response = doctors_table.get_item(Key={'doctor_id': doctor_id})
    doctor = response.get('Item')
    
    if not doctor:
        flash("Doctor not found!", "danger")
        return redirect(url_for('doctors_list'))
        
    return render_template('doctor_details.html', doctor=doctor, is_logged_in=is_logged_in())

# Appointments Page
@app.route('/appointments')
def appointments():
    if not is_logged_in():
        flash("Please log in to view and book appointments.", "info")
        return redirect(url_for('login'))
    
    # Get user's appointments
    response = appointments_table.scan(
        FilterExpression=Attr('patient_email').eq(session['user_email'])
    )
    user_appointments = response.get('Items', [])
    
    # Sort appointments by date/time
    user_appointments.sort(key=lambda x: x.get('appointment_datetime', ''))
    
    # Get all doctors for appointment booking
    response = doctors_table.scan()
    doctors = response.get('Items', [])
    
    return render_template('appointments.html', 
                          appointments=user_appointments, 
                          doctors=doctors,
                          is_logged_in=is_logged_in())

# Book Appointment Route
@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    if not is_logged_in():
        flash("Please log in to book appointments.", "danger")
        return redirect(url_for('login'))
        
    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    reason = request.form['reason']
    
    # Basic validation
    if not doctor_id or not appointment_date or not appointment_time or not reason:
        flash("All fields are required to book an appointment.", "danger")
        return redirect(url_for('appointments'))
    
    # Get doctor details
    response = doctors_table.get_item(Key={'doctor_id': doctor_id})
    doctor = response.get('Item')
    
    if not doctor:
        flash("Selected doctor not found.", "danger")
        return redirect(url_for('appointments'))
    
    # Create appointment datetime string for sorting
    appointment_datetime = f"{appointment_date} {appointment_time}"
    
    # Generate a unique appointment ID
    appointment_id = str(uuid.uuid4())
    
    # Store appointment in DynamoDB
    appointments_table.put_item(
        Item={
            'appointment_id': appointment_id,
            'patient_email': session['user_email'],
            'patient_name': session['user_name'],
            'doctor_id': doctor_id,
            'doctor_name': doctor['name'],
            'doctor_specialty': doctor['specialty'],
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'appointment_datetime': appointment_datetime,
            'reason': reason,
            'status': 'scheduled',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    
    # Send confirmation email to patient
    appointment_confirmation = f"Dear {session['user_name']},\n\nYour appointment with Dr. {doctor['name']} ({doctor['specialty']}) has been scheduled for {appointment_date} at {appointment_time}.\n\nReason: {reason}\n\nPlease arrive 15 minutes before your scheduled time.\n\nBest regards,\nNext Gen Hospital"
    send_email(session['user_email'], "Appointment Confirmation", appointment_confirmation)
    
    flash("Appointment booked successfully!", "success")
    return redirect(url_for('appointments'))

# Cancel Appointment Route
@app.route('/cancel-appointment/<appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    if not is_logged_in():
        flash("Please log in to cancel appointments.", "danger")
        return redirect(url_for('login'))
    
    # Get appointment details
    response = appointments_table.get_item(Key={'appointment_id': appointment_id})
    appointment = response.get('Item')
    
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for('appointments'))
    
    # Verify the appointment belongs to the logged-in user
    if appointment['patient_email'] != session['user_email']:
        flash("You don't have permission to cancel this appointment.", "danger")
        return redirect(url_for('appointments'))
    
    # Update appointment status
    appointments_table.update_item(
        Key={'appointment_id': appointment_id},
        UpdateExpression="SET #status = :status, cancelled_at = :cancelled_at",
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'cancelled',
            ':cancelled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    
    # Send cancellation email
    cancellation_message = f"Dear {session['user_name']},\n\nYour appointment with Dr. {appointment['doctor_name']} scheduled for {appointment['appointment_date']} at {appointment['appointment_time']} has been cancelled.\n\nIf you wish to reschedule, please book a new appointment on our website.\n\nBest regards,\nNext Gen Hospital"
    send_email(session['user_email'], "Appointment Cancellation Confirmation", cancellation_message)
    
    flash("Appointment cancelled successfully.", "success")
    return redirect(url_for('appointments'))

# Health Tips Page
@app.route('/health-tips')
def health_tips_page():
    return render_template('health_tips.html', 
                          tips=health_tips, 
                          ailments=common_ailments,
                          is_logged_in=is_logged_in())

# Patient Profile Page
@app.route('/profile')
def patient_profile():
    if not is_logged_in():
        flash("Please log in to view your profile.", "info")
        return redirect(url_for('login'))
    
    # Get patient record
    response = patient_records_table.get_item(Key={'patient_id': session['user_email']})
    patient_record = response.get('Item', {})
    
    # Get user account details
    response = users_table.get_item(Key={'email': session['user_email']})
    user_details = response.get('Item', {})
    
    # Get patient's appointments
    response = appointments_table.scan(
        FilterExpression=Attr('patient_email').eq(session['user_email'])
    )
    appointments = response.get('Items', [])
    
    # Sort appointments by date (newest first)
    appointments.sort(key=lambda x: x.get('appointment_datetime', ''), reverse=True)
    
    return render_template('profile.html', 
                          patient=patient_record, 
                          user=user_details,
                          appointments=appointments,
                          is_logged_in=is_logged_in())

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if not is_logged_in():
        flash("Please log in to update your profile.", "danger")
        return redirect(url_for('login'))

    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        blood_type = request.form.get('blood_type')
        allergies = request.form.get('allergies', '')
        medications = request.form.get('medications', '')

        # Clean up comma-separated string into list
        allergies_list = [a.strip() for a in allergies.split(',') if a.strip()]
        medications_list = [m.strip() for m in medications.split(',') if m.strip()]

        # Update user info in Users table
        users_table.update_item(
            Key={'email': session['user_email']},
            UpdateExpression="SET #name = :name, phone = :phone",
            ExpressionAttributeNames={'#name': 'name'},
            ExpressionAttributeValues={
                ':name': name,
                ':phone': phone
            }
        )

        # Update patient record in PatientRecords table
        patient_records_table.update_item(
            Key={'patient_id': session['user_email']},
            UpdateExpression="""
                SET #name = :name,
                    phone = :phone,
                    blood_type = :blood_type,
                    allergies = :allergies,
                    medications = :medications,
                    last_updated = :last_updated
            """,
            ExpressionAttributeNames={'#name': 'name'},
            ExpressionAttributeValues={
                ':name': name,
                ':phone': phone,
                ':blood_type': blood_type,
                ':allergies': allergies_list,
                ':medications': medications_list,
                ':last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Update session and notify
        session['user_name'] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('patient_profile'))

    except Exception as e:
        app.logger.error(f"Error updating profile: {str(e)}")
        flash("An error occurred while updating your profile.", "danger")
        return redirect(url_for('patient_profile'))


@app.route('/change-password', methods=['POST'])
def change_password():
    # Add your password change logic here
    flash("Password change feature is coming soon!", "info")
    return redirect(url_for('patient_profile'))  # Redirect back to the profile page


# Admin Dashboard (for hospital staff)
@app.route('/admin')
def admin_dashboard():
    if not is_logged_in():
        flash("Please log in to access the admin dashboard.", "danger")
        return redirect(url_for('login'))
    
    # Only allow staff/admin access
    if session['user_type'] not in ['admin', 'staff', 'doctor']:
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('home'))
    
    # Get all appointments
    response = appointments_table.scan()
    all_appointments = response.get('Items', [])
    
    # Get all patients
    response = patient_records_table.scan()
    all_patients = response.get('Items', [])
    
    # Get all doctors
    response = doctors_table.scan()
    all_doctors = response.get('Items', [])
    
    # Get all contact messages
    response = contact_messages_table.scan()
    all_messages = response.get('Items', [])
    
    # Sort data
    all_appointments.sort(key=lambda x: x.get('appointment_datetime', ''), reverse=True)
    all_patients.sort(key=lambda x: x.get('name', ''))
    all_doctors.sort(key=lambda x: x.get('name', ''))
    all_messages.sort(key=lambda x: x.get('submitted_date', ''), reverse=True)
    
    return render_template('admin_dashboard.html', 
                          appointments=all_appointments, 
                          patients=all_patients,
                          doctors=all_doctors,
                          messages=all_messages,
                          is_logged_in=is_logged_in())

# Add Doctor (Admin function)
@app.route('/add-doctor', methods=['GET', 'POST'])
def add_doctor():
    if not is_logged_in() or session['user_type'] != 'admin':
        flash("You don't have permission to add doctors.", "danger")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Generate a unique doctor ID
        doctor_id = str(uuid.uuid4())
        
        # Get form data
        name = request.form['name']
        email = request.form['email']
        specialty = request.form['specialty']
        qualification = request.form['qualification']
        experience = request.form['experience']
        bio = request.form['bio']
        phone = request.form['phone']
        
        # Store doctor in DynamoDB
        doctors_table.put_item(
            Item={
                'doctor_id': doctor_id,
                'name': name,
                'email': email,
                'specialty': specialty,
                'qualification': qualification,
                'experience': experience,
                'bio': bio,
                'phone': phone,
                'available': True,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
        # Also create user account for doctor
        hashed_password = hashpw("temppassword123".encode('utf-8'), gensalt()).decode('utf-8')
        users_table.put_item(
            Item={
                'email': email,
                'name': name,
                'password': hashed_password,
                'phone': phone,
                'user_type': 'doctor',
                'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
        # Send welcome email with login details
        welcome_message = f"Dear Dr. {name},\n\nYou have been added to the Next Gen Hospital portal. You can now login with the following details:\n\nEmail: {email}\nTemporary Password: temppassword123\n\nPlease change your password after first login.\n\nBest regards,\nNext Gen Hospital Administration"
        send_email(email, "Welcome to Next Gen Hospital Portal", welcome_message)
        
        flash(f"Doctor {name} added successfully!", "success")
        return redirect(url_for('doctors_list'))
        
    return render_template('add_doctor.html', is_logged_in=is_logged_in())

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', is_logged_in=is_logged_in()), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', is_logged_in=is_logged_in()), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
