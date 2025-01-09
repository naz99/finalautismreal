import streamlit as st
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# Function to create a SQLite database and table for user accounts
def create_user_db():
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    
    # Create a new table with the new schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            role TEXT NOT NULL DEFAULT 'user'  -- New role column
        )
    ''')
    
    # Copy data from the old table to the new table
    cursor.execute('''
        INSERT INTO new_users (id, username, password, phone, address)
        SELECT id, username, password, phone, address FROM users
    ''')
    
    # Drop the old table
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # Rename the new table to the original table name
    cursor.execute('ALTER TABLE new_users RENAME TO users')
    
    conn.commit()
    conn.close()

# Function to create a SQLite database and table for chat messages
def create_chat_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to register a new user with role
def register_user(username, password, role='user'):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Function to verify user credentials
def verify_user(username, password):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to reset the password
def reset_password(username, new_password):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
    conn.commit()
    conn.close()

# Function to update the username
def update_username(old_username, new_username):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET username = ? WHERE username = ?', (new_username, old_username))
    conn.commit()
    conn.close()

# Function to update user profile with phone number and address
def update_user_profile(username, phone, address):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET phone = ?, address = ? WHERE username = ?', (phone, address, username))
    conn.commit()
    conn.close()

# Function to delete the user account
def delete_user_account(username):
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Function to send a message
def send_message(username, message):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
    conn.commit()
    conn.close()

# Function to retrieve messages
def get_messages():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, message, timestamp FROM messages ORDER BY timestamp')
    messages = cursor.fetchall()
    conn.close()
    return messages

def draw_wrapped_text(canvas, text, x, y, max_width):
    """Draws wrapped text on the canvas."""
    canvas.setFont("Helvetica", 12)
    lines = text.split(' ')
    current_line = ''
    for word in lines:
        test_line = f"{current_line} {word}".strip()
        if canvas.stringWidth(test_line, "Helvetica", 12) < max_width:
            current_line = test_line
        else:
            canvas.drawString(x, y, current_line)
            current_line = word
            y -= 14  # Move down for the next line
    if current_line:
        canvas.drawString(x, y, current_line)

# Function to create a PDF report
def create_pdf(score, responses, username):
    buffer = io.BytesIO()
    p = canvas.Canvas (buffer, pagesize=letter)
    width, height = letter

    # Set font for the title
    p.setFont("Helvetica-Bold", 24)
    
    # Calculate the width of the title text
    title = "Autism Spectrum Disorder (ASD) Traits Test Result"
    title_width = p.stringWidth(title, "Helvetica-Bold", 24)
    
    # Draw the title centered
    p.drawString((width - title_width) / 2, height - 50, title)

    # Set font for the rest of the text
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 100, f"Username: {username}")
    p.drawString(100, height - 120, f"Total Score: {score}/10")
    p.drawString(100, height - 140, "Details of Your Responses:")

    y_position = height - 160
    for i, response in enumerate(responses):
        p.drawString(100, y_position, f"Question {i + 1}: {response}")
        y_position -= 20

    # Add risk assessment based on score
    if score > 3:
        risk_message = "Score indicates high risk. You should bring your child to a health care provider and early intervention provider for a full assessment. For resources in your area, see our website's list of Autism Treatment Network clinics and state-by-state Resource Guide. You can also call or email our Autism Response Team: 888-AUTISM2 (288-4762) or help@autismspeaks.org. The M-CHAT-R is a screening tool, and because no screening tool is perfect, research recommends that the original 20 questions include a Follow-Up Interview. It can be found at: http://www.mchatscreen.com. This questionnaire is designed to screen for autism, not other developmental issues. If you have concerns about any area of your child's development or behavior, please discuss these concerns with your child's doctor."
    else:
        risk_message = "Score indicates low risk. Your child has a low risk of autism spectrum disorder."

    # Draw the risk message in bold
    p.setFont("Helvetica-Bold", 12)
    draw_wrapped_text(p, risk_message, 100, y_position, width - 200)
    y_position -= 20  # Move down for the next line

    # Set font back to normal for the rest of the text
    p.setFont("Helvetica", 12)

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Home page
def home_page():
    st.title("Welcome to the Autism Traits Test ")
    st.markdown("""
    <h3 style='font-size: 20px;background-color: yellow; padding: 5px; border-radius: 5px;'>Use the sidebar to navigate through the app.</h3>""", unsafe_allow_html=True)
    st.markdown("""
    <h3 style='font-size: 20px;'>Dataset Name: Autistic Spectrum Disorder Screening Data for Toddlers</h3>
    <h3 style='font-size: 18px;'>Date: July 22, 2018</h3>
    <h4 style='font-size: 18px;'>Source: Dr. Fadi Thabtah from Department of Digital Technology, Manukau Institute of Technology, Auckland, New Zealand.</h4>
    <h3 style='font-size: 20px;background-color: yellow; padding: 5px; border-radius: 5px;'>DISCLAIMMER!</h3>""", unsafe_allow_html=True)
    st.markdown("""
<h4 style='font-size : 18px;'>These tests are not diagnostic tools rather they are behavioural tests that just pinpoint to autistic traits.</h4>
""", unsafe_allow_html=True)

# Autism Information Page
def autism_info_page():
    st.markdown("""
        <style>
            .big-title {
                font-size: 40px;
            }
            .big-header {
                font-size: 30px;
            }
            .big-text {
                font-size: 25px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="big-title">Information About Autism</h1>', unsafe_allow_html=True)
    st.markdown('<p class="big-text">Autism Spectrum Disorder (ASD) is a complex developmental condition involving persistent challenges in social interaction, speech and nonverbal communication, and restricted/repetitive behaviors.</p>', unsafe_allow_html=True)
    st.markdown('<h2 class="big-header">Key Facts</h2>', unsafe_allow_html=True)
    st.markdown("""
        <ul class="big-text">
            <li >Autism affects individuals differently and to varying degrees.</li>
            <li>Early diagnosis and intervention can significantly improve outcomes.</li>
            <li>Support and resources are available for individuals with autism and their families.</li>
        </ul>
    """, unsafe_allow_html=True)
    st.header("Resources")
    st.write("""
    - [Autism Speaks](https://www.autismspeaks.org)
    - [Persatuan Autisme Malaysia NASOM MELAKA](https://www.nasommelaka.com/)
    - [CDC Autism Spectrum Disorder](https://www.cdc.gov/ncbddd/autism/index.html)
    - [An accessible and efficient autism screening method for behavioural data and predictive analyses](https://journals.sagepub.com/doi/epdf/10.1177/1460458218796636?src=getftr&utm_source=sciencedirect_contenthosting&getft_integrator=sciencedirect_contenthosting)
    - [Autism Behavioral Center](https://abcautism.com.my/)
    """)

# Function for the ASD Traits Prediction Page
def asd_prediction_page():
    st.markdown("<h1 style='font-size: 70px;'>Autism Spectrum Disorder (ASD) Traits Test</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <p style='font-size: 30px; line-height: 1.8;'>
        This test is based on the Q-Chat-10 framework, designed to identify potential Autism Spectrum Disorder (ASD) traits. 
        There are <strong>10 questions</strong> where you will respond with one of the following options: 
        <em>Always, Usually, Sometimes, Rarely, or Never.</em>
        </p>
        <p style='font-size: 30px; line-height: 1.8;'>
        <span style='background-color: yellow; font-weight: bold;'>Scoring:</span><br>
        - For questions 1-9 (A1-A9), if your response is <em>Sometimes, Quite difficult, A few times a week, slightly unusual, less than once a week, Very difficult Rarely, or Never</em>, a score of <strong>1</strong> is assigned.<br>
        - For question 10 (A10), if your response is <em>Always, Very easy, Many times a day, Very typical Usually, or Sometimes</em>, a score of <strong>1</strong> is assigned.<br>
        </p>
        <p style='font-size: 30px; line-height: 1.8;'>
        Add up your scores for all 10 questions. If your total score is <strong>more than 3</strong>, there is a possibility of ASD traits. 
        Otherwise, no ASD traits are observed.
        </p>
    """, unsafe_allow_html=True)

    questions = [
        "Does your child look at you when you call his/her name? / Adakah anak anda memandang kepada anda apabila anda memanggil nama mereka? " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Always/Usually , 1 = Sometimes/Rarely/Never):</h2>",
        
        "How easy is it for you to get eye contact with your child? / Sejauh mana mudah bagi anda untuk mendapatkan hubungan mata dengan anak anda? " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Very easy/Quite easy , 1 = Quite difficult/Very difficult/Impossible):</h2>",
        
        "Does your child point to indicate that s/he wants something? (e.g. a toy that is out of reach) / Adakah anak anda menunjuk untuk menunjukkan bahawa mereka mahu sesuatu? (contohnya mainan yang berada di luar jangkauan) " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Many times a day/A few times a day , 1 = A few times a week/Less than once a week/Never):</h2>",
        
        "Does your child point to share interest with you? (e.g. pointing at an interesting sight) / Adakah anak anda menunjuk untuk berkongsi minat dengan anda? (contohnya menunjuk kepada pemandangan yang menarik) " +
        "<h2 style='font-size: 19px; background-color: white; padding : 5px; border-radius: 5px; margin-top: 15px'>(0 = Many times a day/A few times a day , 1 = A few times a week/Less than once a week/Never):</h2>",
        
        "Does your child pretend? (e.g. care for dolls, talk on a toy phone) / Adakah anak anda berpura-pura? (contohnya menjaga anak patung, bercakap menggunakan telefon mainan) " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Many times a day/A few times a day , 1 = A few times a week/Less than once a week/Never):</h2>",
        
        "Does your child follow where you’re looking? / Adakah anak anda mengikuti tempat yang anda pandang? " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Many times a day/A few times a day , 1 = A few times a week/Less than once a week/Never):</h2>",
        
        "If you or someone else in the family is visibly upset, does your child show signs of wanting to comfort them? (e.g. stroking hair, hugging them) / Jika anda atau seseorang dalam keluarga kelihatan tertekan, adakah anak anda menunjukkan tanda-tanda ingin menenangkan mereka? (contohnya, mengusap rambut, memeluk mereka) " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Always/Usually , 1 = Sometimes/Rarely/Never):</h2>",
        
        "Would you describe your child’s first words as: / Adakah anda menggambarkan perkataan pertama anak anda sebagai: " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Very typical/Quite typical , 1 = Slightly unusual/Very unusual/My child doesn't speak):</h2>",
        
        "Does your child use simple gestures? (e.g. wave goodbye) / Adakah anak anda menggunakan isyarat mudah? (contohnya melambai selamat tinggal) " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Many times a day/A few times a day , 1 = A few times a week/Less than once a week/Never):</h2>",
        
        "Does your child stare at nothing with no apparent purpose? / Adakah anak anda merenung ke arah sesuatu tanpa tujuan yang jelas? " +
        "<h2 style='font-size: 19px; background-color: white; padding: 5px; border-radius: 5px; margin-top: 15px'>(0 = Less than once a week/Never , 1 = Many times a day/A few times a day/A few times a week):</h2>"
    ]
    
    responses = []  # Initialize an empty list to store answers
    
    # Render each question with increased font size
    for i, question in enumerate(questions):
        st.markdown(f"<h3 style='font-size: 28px; font-weight: bold; text-decoration: underline;'>Question {i+1}:</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size: 21px;'>{question}</h3>", unsafe_allow_html=True)
        
        # Append the answer (0 or 1) for each question to the responses list
        response = int(st.selectbox(f" {i}: ", ['0', '1']))
        responses.append(response)

    # Additional user information (optional)
    st.header("Additional User Information")
    st.markdown("<h2 style='font-size: 28px; background-color: yellow; padding: 5px; border-radius: 5px;'>This additional user information doesn't affect the prediction of autism traits. Only works as additional information about the children</h2>", unsafe_allow_html=True)
  
    st.markdown("<h3 style='font-size: 28px;'>Age (Months)/ Umur (Bulan)</h3>", unsafe_allow_html=True)
    age = st.number_input("", min_value=18, max_value=48 , value=18)

    st.markdown("<h3 style='font-size: 28px;'>Sex/ Jantina</h3>", unsafe_allow_html=True)
    sex = st.selectbox("", options=["Male", "Female", "Other"])

    st.markdown("<h3 style='font-size: 28px;'>Ethnicity/ Etnik</h3>", unsafe_allow_html=True)
    ethnicity = st.selectbox(
        "", 
        options=["Melayu", "Cina", "India", "Orang Asli", 
                 "Bumiputera Sabah", "Bumiputera Sarawak"]
    )

    st.markdown("<h3 style='font-size: 28px;'>Jaundice/ Penyakit Kuning</h3>", unsafe_allow_html=True)
    jaundice = st.selectbox("", options=["Yes", "No"])

    st.markdown("<h3 style='font-size: 28px;'>Family Member with ASD/ Ahli keluarga menghidap ASD</h3>", unsafe_allow_html=True)
    family_asd = st.selectbox("", options=["Yes", "No"], key="family_asd")

    st.markdown("<h3 style='font-size: 28px;'>Who completed the test/ Siapa yang menjawab soalan ini</h3>", unsafe_allow_html=True)
    who_completed = st.selectbox(
        "", 
        options=["Family Member", "Self", "Health Care Professional", "School and NGO"]
    )
    
    # Submit button
    if st.button("Predict"):
        score = sum(responses)  # Sum the list of responses
        result = "Potential ASD Traits" if score > 3 else "No ASD Traits"
        st.success(f"Prediction Result: {result}")

        # Popup effect
        with st.expander("View Prediction Details"):
            st.markdown(f"<h2 style='font-size: 28px;'>Prediction Result: {result}</h2>", unsafe_allow_html=True)
            st.markdown("<h3>Details of Your Responses:</h3>", unsafe_allow_html=True)
            for i, response in enumerate(responses):
                st.markdown(f"*Question {i+1}:* {response}")
            st.markdown(f"*Total Score:* {score}/10")  # Popup to show answers and result
       
        pdf_buffer = create_pdf(score, responses, st.session_state['username'])
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name="asd_traits_report.pdf",
            mime="application/pdf"
        )

# Profile Page with phone number, address, and delete account option
def user_profile():
    st.title(f"Welcome, {st.session_state['username']}!")

    # Display current profile info and allow updates
    conn = sqlite3.connect('user_accounts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (st.session_state['username'],))
    user_info = cursor.fetchone()
    conn.close()

    if user_info:
        phone = st.text_input("Phone Number", value=user_info[3] if len(user_info) > 3 else "")  # Assuming phone is in 4th column
        address = st.text_area("Address", value=user_info[4] if len(user_info) > 4 else "")  # Assuming address is in 5th column
        old_username = st.text_input("Current Username", value=user_info[1])  # Assuming username is in 2nd column
        new_username = st.text_input("New Username")

        if st.button("Update Profile"):
            if phone and address:
                update_user_profile(st.session_state['username'], phone, address)
                st.success("Profile updated successfully!")
            else:
                st.error("Please fill in both phone number and address.")
                
            if new_username and new_username != old_username:
                update_username(old_username, new_username)
                st.session_state['username'] = new_username
                st.success("Username updated successfully!")

        # Option to delete account
        if st.button("Delete Account"):
            confirm = st.checkbox("I confirm that I want to delete my account.")
            if confirm:
                delete_user_account(st.session_state['username'])
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.success("Your account has been deleted.")
                st.rerun()
            else:
                st.warning("Please confirm to delete your account.")

    else:
        st.error("User  not found. Please log in again.")

# User Login Page
def user_login():
    st.title("Welcome,")
    st.title("User  Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login "):
        if verify_user(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Welcome back, {username}!")
        else:
            st.error("Invalid username or password. Please try again.")
    st.write("Please press click LOGIN twice to login ")

# User Registration Page
def user_registration():
    st.title("User  Registration")
    
    # Input fields for registration
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = st.selectbox("Select Role", ["user", "doctor"])  # Role selection

    if password != confirm_password:
        st.error("Passwords do not match.")
    elif password == "" or username == "":
        st.error("Please fill in both username and password.")
    else:
        if st.button("Register"):
            if register_user(username, password, role):
                st.success("User  registered successfully! You can now log in.")
            else:
                st.error("Username already exists. Please choose a different username.")

# Forgot Password Page
def forgot_password():
    st.title("Forgot Password")
    username = st.text_input("Enter your username to reset password")
    new_password = st.text_input("Enter new password", type="password")
    confirm_password = st.text_input("Confirm new password", type="password")

    if new_password == confirm_password:
        if st.button("Reset Password"):
            reset_password(username, new_password)
            st.success("Password reset successfully! You can now log in with the new password.")
    else:
        st.error("Passwords do not match.")

# Chat Page
def chat_page():
    st.title("Live Chat with Doctor")

    # Input for the message
    message = st.text_input("Type your message:")
    
    if st.button("Send"):
        if message:
            send_message(st.session_state['username'], message)
            st.success("Message sent!")
        else:
            st.error("Please enter a message.")

    # Display chat messages
    messages = get_messages()
    for username, message, timestamp in messages:
        st.write(f"{timestamp} - **{username}**: {message}")

    # Doctor's reply section
    if st.session_state.get('is_doctor', False):
        doctor_reply = st.text_input("Type your reply:")
        if st.button("Send Reply"):
            if doctor_reply:
                send_message("Doctor", doctor_reply)  # Assuming "Doctor" is the username for the doctor
                st.success("Reply sent!")
            else:
                st.error("Please enter a reply.")

# Main app page navigation
def main():
    create_user_db()  # Create the user database and table if it doesn't exist
    create_chat_db()  # Create the chat database and table if it doesn't exist

    # Inject custom CSS for background
    st.markdown(
        """
        <style>
        /* Custom background style */
        .stApp {
            background: linear-gradient(to right, #83a4d4, #CDC9FB); /* Light blue to light purple gradient */
            background-attachment: fixed;
            color: black; /* Text color */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Check if the user is logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        # Show the home page first for users who are not logged in
        home_page()

        # Sidebar navigation for login or registration
        st.sidebar.title("User  Authentication")
        page = st.sidebar.selectbox("Select a page", ["Login", "Register", "Forgot Password"])
        
        if page == "Login":
            user_login()
        elif page == "Register":
            user_registration()
        elif page == "Forgot Password":
            forgot_password()
    else:
        # If the user is logged in, show the dashboard options
        st.sidebar.title("User  Dashboard")
        page = st.sidebar.selectbox("Select a page", ["Autism Info", "ASD Prediction", "Profile", "Chat", "Logout"])
        
        if page == "ASD Prediction":
            asd_prediction_page()
        elif page == "Autism Info":
            autism_info_page()
        elif page == "Profile":
            user_profile()
        elif page == "Chat":
            chat_page()
        elif page == "Logout":
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['is_doctor'] = False  # Reset doctor role on logout
            st.success("You have logged out successfully.")
            st.rerun()  # Use rerun to refresh the app state

if __name__ == "__main__":
    main()