import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from openai import OpenAI


# --- CONFIG & INITIALIZATION ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123" # Use your desired password here



# --- CONFIG & INITIALIZATION ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
)

DB_PATH = "data/thesis_data.db"
DATA_FILE = "data/master_thesis_data.csv"
MODEL_NAME = "nvidia/nemotron-3-super-120b-a12b:free"

if not os.path.exists('data'):
    os.makedirs('data')

# --- DATABASE HELPER FUNCTIONS ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create the table with all necessary columns for the thesis
    c.execute('''CREATE TABLE IF NOT EXISTS study_logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 timestamp TEXT, name TEXT, email TEXT, university TEXT, 
                 course TEXT, semester TEXT, question TEXT, 
                 attempt_1 TEXT, attempt_2 TEXT, teach_back TEXT, 
                 ai_feedback TEXT, score_1 TEXT, score_2 TEXT, final_grade TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data_tuple):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO study_logs (timestamp, name, email, university, course, semester, 
                                        question, attempt_1, attempt_2, teach_back, ai_feedback, 
                                        score_1, score_2, final_grade) 
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', data_tuple)
    conn.commit()
    conn.close()

init_db() # Run once on startup

st.set_page_config(page_title="Teach It Back AI", page_icon="🎓", layout="wide")

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "registration"
if 'step' not in st.session_state: st.session_state.step = 1
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'study_session' not in st.session_state: st.session_state.study_session = {}

# --- SIDEBAR ADMIN LOGIN ---
with st.sidebar:
    st.title("🔐 Admin Portal")
    if not st.session_state.admin_logged_in:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login as Admin"):
            if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.session_state.page = "admin_dashboard"
                st.rerun()
            else:
                st.error("Incorrect credentials")
    else:
        if st.button("Open Dashboard"):
            st.session_state.page = "admin_dashboard"
            st.rerun()
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.session_state.page = "registration"
            st.rerun()

# --- PAGE: ADMIN DASHBOARD ---
if st.session_state.page == "admin_dashboard" and st.session_state.admin_logged_in:
    st.title("📂 Master Thesis Admin Dashboard")
    st.info("Authorized Access Only: Reviewing Student Participation Data")

    if st.button("🔄 Refresh Data"):
        st.rerun()

    conn = sqlite3.connect(DB_PATH)
    full_df = pd.read_sql_query("SELECT * FROM study_logs", conn)
    conn.close()

    if not full_df.empty:
        st.metric("Total Research Participants", len(full_df))
        st.dataframe(full_df)
        
        csv = full_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Dataset (CSV)", csv, f"thesis_data_{date.today()}.csv", "text/csv")
    else:
        st.warning("No data found in the database yet.")

    if st.button("⬅️ Back to Student View"):
        st.session_state.page = "registration"
        st.rerun()

# --- PAGE 1: REGISTRATION ---
if st.session_state.page == "registration":
    st.title("🎓 Research Registration")
    st.markdown("Please provide your details to unlock the **Teach It Back** AI tool.")

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name*")
            email = st.text_input("Email ID*")
            mobile = st.text_input("Mobile Number")
        with col2:
            uni = st.text_input("University Name", placeholder="SRH Fürth")
            sem = st.selectbox("Current Semester", ["1st", "2nd", "3rd", "4th", "Thesis Phase", "Passout"])
            dob = st.date_input("Date of Birth", min_value=date(1980, 1, 1))
        
        course_list = [
            "Artificial Intelligence", "Applied Computer Science", "Computer Science", 
            "Business Analytics", "Business Administration", "Biotechnology", 
            "Data Science", "Digital Health", "Medical Process Management", 
            "Machine Learning", "Mechanical Engineering", "Mechatronics", 
            "Civil Engineering", "Electrical Engineering", "Nursing Science", 
            "International Business and Management", "Physics", "Chemistry", 
            "Medical", "Other"
        ]
        selected_course = st.selectbox("Course of Study", options=course_list)
        
        course_final = selected_course
        if selected_course == "Other":
            course_final = st.text_input("Please specify your course")

        col_city, col_country = st.columns(2)
        with col_city:
            city = st.text_input("City", placeholder="Nuremberg")
        with col_country:
            country = st.selectbox("Country", ["Select Country", "Germany", "India", "UK", "USA", "France", "Italy", "Spain", "Other"])

        if st.button("Register & Start Learning"):
            if name and email and course_final:
                st.session_state.user_info = {
                    "Name": name, "Email": email, "Mobile": mobile, "University": uni,
                    "Course": course_final, "Semester": sem, "DOB": str(dob), "Location": f"{city}, {country}"
                }
                st.session_state.page = "ai_tool"
                st.rerun()
            else:
                st.error("Please fill in all required fields (*)")

# --- PAGE 2: TEACH IT BACK AI ---
elif st.session_state.page == "ai_tool":
    st.title("🧠 Teach It Back: AI Learning")
    
    # Simple Progress Bar
    progress_text = f"Step {st.session_state.step} of 5"
    st.progress(st.session_state.step / 5, text=progress_text)
    
    # STEP 1: Question
    if st.session_state.step == 1:
        st.subheader("Step 1: The Topic")
        q = st.text_area("What specific topic or question are you studying?", placeholder="e.g., Explain how a Transformer model works.")
        if st.button("Next Step") and q:
            st.session_state.study_session['question'] = q
            st.session_state.step = 2
            st.rerun()

    # STEP 2: First Attempt
    elif st.session_state.step == 2:
        st.subheader("Step 2: Your Current Knowledge")
        st.write(f"**Topic:** {st.session_state.study_session['question']}")
        ans1 = st.text_area("Try to explain this concept or answer the question now (Don't worry about being perfect!):")
        if st.button("Unlock AI Guidance"):
            if ans1:
                st.session_state.study_session['attempt1'] = ans1
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("Please type your answer first to proceed.")

   # STEP 3: AI Hints (Detailed Scaffolding)
    elif st.session_state.step == 3:
        st.subheader("Step 3: AI Tutor Guidance & Scaffolding")
        if 'hints' not in st.session_state.study_session:
            with st.spinner("AI Tutor is preparing a detailed conceptual breakdown..."):
                # ENHANCED PROMPT: Asking for deep technical scaffolding
                prompt = (
                    f"The student is studying: {st.session_state.study_session['question']}. "
                    f"Their first attempt: {st.session_state.study_session['attempt1']}. "
                    "\n\nINSTRUCTION: Provide a high-depth conceptual guide. "
                    "1. Break the topic into its core technical components. "
                    "2. Explain the logic/mechanism behind these components in detail. "
                    "3. Use analogies if helpful. "
                    "4. DO NOT provide the final summarized answer to the student's specific question, "
                    "but provide all the 'building blocks' so they can synthesize the answer themselves. "
                    "Make the response detailed and educational (at least 200-300 words)."
                )
                
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a supportive University Professor. You teach by explaining deep logic and mechanisms without giving away the final solution directly."},
                        {"role": "user", "content": prompt}
                    ]
                )
                st.session_state.study_session['hints'] = response.choices[0].message.content
        
        # Displaying the detailed hint in a clean format
        st.markdown("### 💡 Conceptual Guidance")
        st.write(st.session_state.study_session['hints'])
        
        st.divider()
        if st.button("I've studied the hints, let's try Attempt 2"):
            st.session_state.step = 4
            st.rerun()

    # STEP 4: Second Attempt
    elif st.session_state.step == 4:
        st.subheader("Step 4: Refined Answer")
        st.write(f"**Topic:** {st.session_state.study_session['question']}")
        ans2 = st.text_area("Using the hints provided, try answering the question again with more detail:")
        if st.button("Proceed to Final Step"):
            if ans2:
                st.session_state.study_session['attempt2'] = ans2
                st.session_state.step = 5
                st.rerun()
            else:
                st.warning("Please write your improved answer.")

# STEP 5: Final Evaluation & Comprehensive Report View
    elif st.session_state.step == 5:
        if 'final_report' not in st.session_state:
            st.subheader("🏁 Final Step: Teach It Like I'm 5 (ELI5)")
            st.write("Explain the concept simply to a beginner. This is the core of the research.")
            teach = st.text_area("Your Explanation:", placeholder="Describe the logic simply...", height=200)
            
            if st.button("Submit & Generate Academic Report"):
                if teach:
                    with st.spinner("AI Professor is conducting a deep-dive evaluation..."):
                        # ENHANCED PROMPT FOR HIGH-DETAIL FEEDBACK
                        eval_prompt = (
                            f"Topic: {st.session_state.study_session['question']}. "
                            f"Attempt 1: {st.session_state.study_session['attempt1']}. "
                            f"Attempt 2: {st.session_state.study_session['attempt2']}. "
                            f"ELI5 explanation: {teach}. "
                            "\n\nCRITICAL: Start your response with exactly this format:\n"
                            "SCORE1: [score]/10\n"
                            "SCORE2: [score]/10\n"
                            "FINAL: [score]/10\n\n"
                            "DETAILED ACADEMIC REPORT:\n"
                            "1. COMPARATIVE ANALYSIS: What specific knowledge was missing in Attempt 1?\n"
                            "2. TECHNICAL ACCURACY: Is the simplified ELI5 explanation actually correct?\n"
                            "3. SCAFFOLDING SUCCESS: How well did the student use the provided hints?\n"
                            "4. CRITICAL FEEDBACK: What areas still need work?\n"
                            "5. SCORE RATIONALE: Why did they receive the scores above?"
                            "RESOURCES:\n"
                                "- [Resource 1: Name of book/doc]\n"
                                "- [Resource 2: Key search term]\n"
                                "- [Resource 3: Practical exercise tip]"
                        )
                        
                        try:
                            eval_res = client.chat.completions.create(
                                model=MODEL_NAME,
                                messages=[
                                    {"role": "system", "content": "You are a senior university professor and academic researcher."},
                                    {"role": "user", "content": eval_prompt}
                                ]
                            )
                            
                            full_res = eval_res.choices[0].message.content
                            st.session_state.final_report = full_res
                            
                            # PARSE SCORES
                            lines = full_res.split('\n')
                            st.session_state.ai_score1 = [l for l in lines if "SCORE1:" in l][0].split(":")[1].strip()
                            st.session_state.ai_score2 = [l for l in lines if "SCORE2:" in l][0].split(":")[1].strip()
                            st.session_state.display_score = [l for l in lines if "FINAL:" in l][0].split(":")[1].strip()

                            # --- SAVE TO DATABASE (Master Research Record) ---
                            import sqlite3
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            c.execute('''INSERT INTO study_logs (timestamp, name, email, university, course, semester, 
                                                                question, attempt_1, attempt_2, teach_back, 
                                                                ai_feedback, score_1, score_2, final_grade) 
                                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                      (pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                       st.session_state.user_info['Name'], st.session_state.user_info['Email'], 
                                       st.session_state.user_info['University'], st.session_state.user_info['Course'], 
                                       st.session_state.user_info['Semester'], st.session_state.study_session['question'], 
                                       st.session_state.study_session['attempt1'], st.session_state.study_session['attempt2'], 
                                       teach, full_res, st.session_state.ai_score1, st.session_state.ai_score2, st.session_state.display_score))
                            conn.commit()
                            conn.close()
                            st.rerun()

                        except Exception as e:
                            st.error(f"Authentication/API Error: {e}. Check OpenRouter API Key and Balance.")
                else:
                    st.warning("Please provide your simplified explanation.")
        
        else:
            # --- FINAL REPORT VIEW ---
            st.balloons()
            st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📊 Thesis Learning Analysis</h1>", unsafe_allow_html=True)
            
            # --- DYNAMIC DELTA CALCULATION ---
            try:
                # Extracting numbers from strings like "7/10" or "7"
                val1 = float(st.session_state.ai_score1.split('/')[0])
                val2 = float(st.session_state.ai_score2.split('/')[0])
                diff = val2 - val1
                
                if diff > 0:
                    delta_label = f"+{diff} Improvement"
                elif diff < 0:
                    delta_label = f"{diff} Decrease"
                else:
                    delta_label = "No Change"
            except:
                delta_label = "Score change unavailable"

            # Metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a: 
                st.metric(label="Initial Attempt", value=st.session_state.ai_score1)
            with col_b: 
                # This will now show RED for negative and GREEN for positive automatically
                st.metric(label="Refined Attempt", value=st.session_state.ai_score2, delta=delta_label)
            with col_c: 
                st.metric(label="Final Learning Grade", value=st.session_state.display_score)

            st.divider()

            # Side-by-Side Table
            st.subheader("📝 Content Evolution")
            st.table(pd.DataFrame({
                "Evaluation Phase": ["Pre-Hint (Attempt 1)", "Post-Hint (Attempt 2)"],
                "Response Detail": [st.session_state.study_session['attempt1'], st.session_state.study_session['attempt2']]
            }))

            # 3. Highlighted Feedback Box
            st.subheader("📋 Professor's Detailed Rationale")
            
            report_text = st.session_state.final_report
            main_feedback = report_text.split("RESOURCES:")[0] if "RESOURCES:" in report_text else report_text
            
            st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 30px; border-radius: 15px; border-left: 10px solid #4CAF50; color: white; margin-bottom: 20px;">
                {main_feedback.replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)

            # 4. Personalized Learning Path (The Resources)
            st.divider()
            st.subheader("🚀 Your Personalized Learning Path")

            if "RESOURCES:" in report_text:
                resources_part = report_text.split("RESOURCES:")[1]
                st.success("The AI Tutor recommends these specific materials to bridge your knowledge gaps:")
                st.markdown(f"""
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; color: #1b5e20;">
                    <h4 style="margin-top:0;">📚 Suggested Study Materials:</h4>
                    {resources_part.replace('\n', '<br>')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Complete the evaluation to see personalized study recommendations.")

            st.divider()
            
            # Reset Buttons
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Study New Topic", use_container_width=True):
                    st.session_state.step = 1
                    st.session_state.study_session = {}
                    if 'final_report' in st.session_state: del st.session_state.final_report
                    st.rerun()
            with c2:
                if st.button("🚪 Logout Student", use_container_width=True):
                    st.session_state.page = "registration"
                    st.session_state.step = 1
                    st.session_state.user_info = {}
                    st.session_state.study_session = {}
                    if 'final_report' in st.session_state: del st.session_state.final_report
                    st.rerun()