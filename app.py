import streamlit as st
from resume_utils import analyze_resume
from streamlit_tags import st_tags

#with open("custom_streamlit_style.css") as f:
 #   st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#https://www.transparenttextures.com/patterns/cubes.png
#st.markdown("""
#<style>
#.stApp {
 #   background-image: url(""C:/Users/Heer Patel/Downloads/ChatGPT Image Jul 28, 2025, 08_41_51 PM.png"");
  #  background-color: #f4f8fb;
   # background-size: cover;
#}
#</style>
#""", unsafe_allow_html=True)

st.set_page_config(page_title="AI Resume Critique", layout="centered")

st.title("🧠 AI Resume Critique Tool")

uploaded_file = st.file_uploader("📄 Upload your Resume (PDF)", type=["pdf"])

if uploaded_file:
    result = analyze_resume(uploaded_file)

    st.success(f"👋 Hello {result['name']}")
    # Basic Info
    #st.markdown(f"""
    #<div class='info-card'>
     #   <strong>🧑 Name:</strong> {result['name']}<br>
      #  <strong>📧 Email:</strong> <a style='color:#4db8ff;' href='mailto:{result['email']}'>{result['email']}</a>
    #</div>
    #""", unsafe_allow_html=True)

    st.markdown(f"""
<div style="background-color: #111827; padding: 20px; border-radius: 12px; border: 1px solid #4b5563; margin-bottom: 20px;">
    <h4 style="color:#10b981;">🧾 Your Basic Info</h4>
    <p><strong>Name:</strong> {result['name']}</p>
    <p><strong>Email:</strong> <a href='mailto:{result['email']}' style="color:#3b82f6;">{result['email']}</a></p>
</div>
""", unsafe_allow_html=True)


    #st.subheader("Your Basic Info")
    #st.markdown(f"**Name:** {result['name']}")
    #st.markdown(f"**Email:** {result['email']}")

    # Dynamic Level Display
    level_color = {
        "Beginner": "#dc3545",       # Red
        "Intermediate": "#ffc107",   # Orange
        "Advanced": "#28a745"        # Green
    }
    level = result["level"]
    color = level_color.get(level, "#17a2b8")
    st.markdown(f"✅<span style='color:{color}; font-size:18px; font-weight:bold;'>You are at **{level}** level!</span>", unsafe_allow_html=True)
    
    st.subheader("Skills Recommendation 💡")
    skills_in_resume=result["skills_in_resume"]
    keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=skills_in_resume, key='1')

    #st.markdown("### Skills that you have")
    #or skill in result['skills_in_resume']:
      #  st.markdown(f"<span style='background-color:#007bff;color:white;padding:4px 8px;border-radius:6px;margin:2px;display:inline-block'>{skill}</span>", unsafe_allow_html=True)

    st.success(f"Our analysis says you are looking for **{result['job_target']}**")

    recommended_skills = result["recommended_skills"]
    recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
    #st.markdown("### Recommended skills for you")
    #for skill in result['recommended_skills']:
     #   st.markdown(f"<span style='background-color:#dc3545;color:white;padding:4px 8px;border-radius:6px;margin:2px;display:inline-block'>{skill}</span>", unsafe_allow_html=True)

    st.markdown("💡 <span style='color:green;'>Adding these skills to resume will boost the chances of getting a Job.</span>", unsafe_allow_html=True)

    #st.subheader("Courses & Certificates 🎓 Recommendations")
    #num_courses = st.slider("Choose Number of Course Recommendations:", 1, 10, 4)
    #for i, course in enumerate(result['courses'][:num_courses]):
     #   st.markdown(f"{i+1}) [{course['title']} by {course['provider']}]({course['url']})")

    st.subheader("Resume Tips & Ideas 💡")
    for tip in result['resume_tips']:
        st.markdown(f"🔹 {tip}")

    st.subheader("Resume Score 📝")
    score = result['ats_score']
    st.progress(score)
    st.success(f"Your Resume Writing Score: {score}/100")
    st.caption("Note: This score is calculated based on the content and format of your resume.")
else:
    st.info("👆 Please upload your PDF resume to start the analysis.")
