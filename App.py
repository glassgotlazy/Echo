import streamlit as st
import openai
import requests
import json
import time
from datetime import datetime
import pandas as pd
import os

# Page configuration
st.set_page_config(
    page_title="EduSearch Pro - Student Learning Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #4CAF50;
    }
    
    .quiz-question {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196F3;
    }
    
    .correct-answer {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .wrong-answer {
        background: #ffebee;
        color: #c62828;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .score-display {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'topic_content' not in st.session_state:
        st.session_state.topic_content = ""
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

# OpenAI API setup
def setup_openai():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OpenAI API key not found. Please add it to Streamlit secrets or environment variables.")
        st.stop()
    openai.api_key = api_key

# Function to search for topic information
def search_topic_info(topic, subject=None):
    try:
        prompt = f"""
        Provide comprehensive educational content about "{topic}" {f"in {subject}" if subject else ""}.
        
        Structure your response as follows:
        
        ## Overview
        Provide a clear, concise introduction to the topic.
        
        ## Key Concepts
        List and explain the main concepts, theories, or principles.
        
        ## Important Details
        Provide detailed explanations, formulas, examples, or case studies.
        
        ## Real-world Applications
        Explain how this topic is applied in real life or industry.
        
        ## Study Tips
        Provide specific tips for understanding and remembering this topic.
        
        Keep the content educational, accurate, and suitable for students.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert educational tutor helping students learn various subjects."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error fetching topic information: {str(e)}")
        return None

# Function to generate quiz questions
def generate_quiz(topic, subject=None, difficulty="medium", num_questions=5):
    try:
        prompt = f"""
        Create {num_questions} multiple-choice questions about "{topic}" {f"in {subject}" if subject else ""} 
        at {difficulty} difficulty level.
        
        Format each question as a JSON object with this structure:
        {{
            "question": "The question text",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A",
            "explanation": "Brief explanation of why this is correct"
        }}
        
        Return ONLY a JSON array of {num_questions} question objects. No additional text.
        Make sure questions test understanding, not just memorization.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert quiz generator creating educational assessments."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.8
        )
        
        quiz_text = response.choices[0].message.content.strip()
        quiz_questions = json.loads(quiz_text)
        return quiz_questions
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

# Function to save search history
def save_search_history(topic, subject, timestamp):
    search_entry = {
        "topic": topic,
        "subject": subject or "General",
        "timestamp": timestamp
    }
    st.session_state.search_history.append(search_entry)
    
    # Keep only last 10 searches
    if len(st.session_state.search_history) > 10:
        st.session_state.search_history = st.session_state.search_history[-10:]

# Main application
def main():
    initialize_session_state()
    setup_openai()
    
    # Header
    st.markdown('<h1 class="main-header">🎓 EduSearch Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Your AI-Powered Learning Companion")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Learning Tools")
        
        # Navigation
        page = st.selectbox(
            "Choose your learning mode:",
            ["🔍 Topic Explorer", "📝 Quiz Generator", "📊 Learning Dashboard", "📚 Study History"]
        )
        
        st.divider()
        
        # Quick stats
        if st.session_state.search_history:
            st.subheader("📈 Your Progress")
            st.metric("Topics Explored", len(st.session_state.search_history))
            st.metric("Last Study Session", st.session_state.search_history[-1]["timestamp"][:10] if st.session_state.search_history else "None")
    
    # Main content based on selected page
    if page == "🔍 Topic Explorer":
        topic_explorer_page()
    elif page == "📝 Quiz Generator":
        quiz_generator_page()
    elif page == "📊 Learning Dashboard":
        learning_dashboard_page()
    elif page == "📚 Study History":
        study_history_page()

def topic_explorer_page():
    st.header("🔍 Topic Explorer")
    st.markdown("Search for any topic and get comprehensive learning materials!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_input("🎯 Enter the topic you want to learn about:", placeholder="e.g., Photosynthesis, Calculus, World War II")
    
    with col2:
        subject = st.selectbox("📚 Subject (Optional):", 
                              ["", "Mathematics", "Physics", "Chemistry", "Biology", "History", 
                               "Literature", "Computer Science", "Economics", "Psychology"])
    
    if st.button("🔍 Search Topic", type="primary"):
        if topic.strip():
            with st.spinner("🔄 Searching for comprehensive information..."):
                content = search_topic_info(topic, subject)
                
                if content:
                    st.session_state.topic_content = content
                    save_search_history(topic, subject, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    
                    st.success(f"✅ Found comprehensive information about: **{topic}**")
                    
                    # Display content in an organized way
                    st.markdown("---")
                    st.markdown(content)
                    
                    # Quick action buttons
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📝 Generate Quiz"):
                            st.session_state.current_topic = topic
                            st.session_state.current_subject = subject
                            st.rerun()
                    
                    with col2:
                        if st.button("📋 Copy Content"):
                            st.code(content)
                    
                    with col3:
                        if st.button("💾 Save Notes"):
                            st.download_button(
                                label="Download as Text",
                                data=content,
                                file_name=f"{topic.replace(' ', '_')}_notes.txt",
                                mime="text/plain"
                            )
        else:
            st.warning("⚠️ Please enter a topic to search!")

def quiz_generator_page():
    st.header("📝 Quiz Generator")
    st.markdown("Test your knowledge with AI-generated quizzes!")
    
    if not hasattr(st.session_state, 'current_topic'):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            topic = st.text_input("🎯 Enter topic for quiz:", placeholder="e.g., Photosynthesis, Algebra, Shakespeare")
        
        with col2:
            subject = st.selectbox("📚 Subject:", 
                                  ["", "Mathematics", "Physics", "Chemistry", "Biology", "History", 
                                   "Literature", "Computer Science", "Economics", "Psychology"])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            difficulty = st.selectbox("🎚️ Difficulty:", ["easy", "medium", "hard"])
        
        with col2:
            num_questions = st.slider("❓ Number of Questions:", min_value=3, max_value=10, value=5)
        
        with col3:
            st.write("")  # Spacing
            if st.button("🎯 Generate Quiz", type="primary"):
                if topic.strip():
                    with st.spinner("🔄 Generating your personalized quiz..."):
                        questions = generate_quiz(topic, subject, difficulty, num_questions)
                        
                        if questions:
                            st.session_state.quiz_questions = questions
                            st.session_state.current_question = 0
                            st.session_state.user_answers = []
                            st.session_state.quiz_completed = False
                            st.success("✅ Quiz generated successfully!")
                            st.rerun()
                else:
                    st.warning("⚠️ Please enter a topic for the quiz!")
    
    # Display quiz if questions exist
    if st.session_state.quiz_questions and not st.session_state.quiz_completed:
        display_quiz()
    elif st.session_state.quiz_completed:
        display_quiz_results()

def display_quiz():
    questions = st.session_state.quiz_questions
    current_q = st.session_state.current_question
    
    if current_q < len(questions):
        question = questions[current_q]
        
        # Progress bar
        progress = (current_q + 1) / len(questions)
        st.progress(progress)
        st.write(f"Question {current_q + 1} of {len(questions)}")
        
        # Question display
        st.markdown(f'<div class="quiz-question"><h3>{question["question"]}</h3></div>', 
                   unsafe_allow_html=True)
        
        # Answer options
        user_answer = st.radio(
            "Choose your answer:",
            question["options"],
            key=f"question_{current_q}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if current_q > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            if st.button("➡️ Next" if current_q < len(questions) - 1 else "🏁 Finish Quiz"):
                # Save answer
                if len(st.session_state.user_answers) <= current_q:
                    st.session_state.user_answers.append(user_answer[0])  # Get letter only
                else:
                    st.session_state.user_answers[current_q] = user_answer[0]
                
                if current_q < len(questions) - 1:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                
                st.rerun()

def display_quiz_results():
    questions = st.session_state.quiz_questions
    user_answers = st.session_state.user_answers
    
    # Calculate score
    correct_count = sum(1 for i, q in enumerate(questions) 
                       if i < len(user_answers) and user_answers[i] == q["correct_answer"])
    total_questions = len(questions)
    score_percentage = (correct_count / total_questions) * 100
    
    # Display score
    if score_percentage >= 80:
        score_color = "#4CAF50"
        emoji = "🎉"
        message = "Excellent work!"
    elif score_percentage >= 60:
        score_color = "#FF9800"
        emoji = "👍"
        message = "Good job!"
    else:
        score_color = "#f44336"
        emoji = "📚"
        message = "Keep studying!"
    
    st.markdown(f"""
    <div class="score-display" style="background-color: {score_color}20; color: {score_color};">
        {emoji} {message}<br>
        Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed results
    st.subheader("📊 Detailed Results")
    
    for i, question in enumerate(questions):
        user_answer = user_answers[i] if i < len(user_answers) else "Not answered"
        correct_answer = question["correct_answer"]
        is_correct = user_answer == correct_answer
        
        with st.expander(f"Question {i+1}: {'✅' if is_correct else '❌'}"):
            st.write(f"**Question:** {question['question']}")
            st.write(f"**Your answer:** {user_answer}")
            st.write(f"**Correct answer:** {correct_answer}")
            st.write(f"**Explanation:** {question['explanation']}")
            
            if is_correct:
                st.markdown('<div class="correct-answer">✅ Correct!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="wrong-answer">❌ Incorrect</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retake Quiz"):
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            st.session_state.quiz_completed = False
            st.rerun()
    
    with col2:
        if st.button("📝 New Quiz"):
            st.session_state.quiz_questions = []
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            st.session_state.quiz_completed = False
            if hasattr(st.session_state, 'current_topic'):
                delattr(st.session_state, 'current_topic')
            st.rerun()
    
    with col3:
        # Download results
        results_text = f"Quiz Results\n\nScore: {correct_count}/{total_questions} ({score_percentage:.1f}%)\n\n"
        for i, q in enumerate(questions):
            results_text += f"Q{i+1}: {q['question']}\n"
            results_text += f"Your answer: {user_answers[i] if i < len(user_answers) else 'Not answered'}\n"
            results_text += f"Correct: {q['correct_answer']}\n\n"
        
        st.download_button(
            label="📄 Download Results",
            data=results_text,
            file_name=f"quiz_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def learning_dashboard_page():
    st.header("📊 Learning Dashboard")
    st.markdown("Track your learning progress and insights!")
    
    if not st.session_state.search_history:
        st.info("🔍 Start exploring topics to see your learning analytics here!")
        return
    
    # Create dataframe from search history
    df = pd.DataFrame(st.session_state.search_history)
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Topics Studied", len(df))
    
    with col2:
        unique_subjects = df['subject'].nunique()
        st.metric("🔬 Subjects Covered", unique_subjects)
    
    with col3:
        days_active = df['date'].nunique()
        st.metric("📅 Days Active", days_active)
    
    with col4:
        avg_per_day = len(df) / max(days_active, 1)
        st.metric("⚡ Avg Topics/Day", f"{avg_per_day:.1f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Study Activity")
        daily_counts = df.groupby('date').size().reset_index(name='count')
        st.line_chart(daily_counts.set_index('date'))
    
    with col2:
        st.subheader("🔬 Subject Distribution")
        subject_counts = df['subject'].value_counts()
        st.bar_chart(subject_counts)
    
    # Recent activity
    st.subheader("🕒 Recent Learning Activity")
    recent_df = df.tail(5)[['topic', 'subject', 'timestamp']]
    st.dataframe(recent_df, use_container_width=True)

def study_history_page():
    st.header("📚 Study History")
    st.markdown("Review your learning journey!")
    
    if not st.session_state.search_history:
        st.info("🔍 No study history yet. Start exploring topics!")
        return
    
    # Search and filter options
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("🔍 Search topics:", placeholder="Search your studied topics...")
    
    with col2:
        subject_filter = st.selectbox("Filter by subject:", 
                                     ["All"] + list(set([h['subject'] for h in st.session_state.search_history])))
    
    # Filter history
    filtered_history = st.session_state.search_history
    
    if search_term:
        filtered_history = [h for h in filtered_history if search_term.lower() in h['topic'].lower()]
    
    if subject_filter != "All":
        filtered_history = [h for h in filtered_history if h['subject'] == subject_filter]
    
    # Display history
    if filtered_history:
        for i, entry in enumerate(reversed(filtered_history)):
            with st.expander(f"📖 {entry['topic']} - {entry['subject']} ({entry['timestamp']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Topic:** {entry['topic']}")
                    st.write(f"**Subject:** {entry['subject']}")
                    st.write(f"**Studied on:** {entry['timestamp']}")
                
                with col2:
                    if st.button(f"🔄 Study Again", key=f"study_again_{i}"):
                        # Redirect to topic explorer with this topic
                        st.session_state.current_topic = entry['topic']
                        st.session_state.current_subject = entry['subject']
                        st.switch_page("Topic Explorer")
    else:
        st.info("No topics found matching your criteria.")
    
    # Clear history option
    if st.session_state.search_history:
        st.divider()
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.button("⚠️ Confirm Clear History"):
                st.session_state.search_history = []
                st.success("History cleared!")
                st.rerun()

if __name__ == "__main__":
    main()
