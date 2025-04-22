import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
from faker import Faker

# Initialize faker for dummy data
fake = Faker()

# Set page config
st.set_page_config(
    page_title="Employee Wellness Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Generate dummy data for multiple department managers
def generate_dummy_data():
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Product']
    roles = ['Manager', 'Senior', 'Mid-level', 'Junior']
    
    employees = []
    for i in range(50):
        dept = random.choice(departments)
        role = random.choice(roles)
        employees.append({
            'id': i+1,
            'name': fake.name(),
            'department': dept,
            'role': role,
            'email': fake.email(),
            'join_date': fake.date_between(start_date='-5y', end_date='today'),
            'manager': random.choice([True, False]) if role == 'Manager' else False
        })
    
    # Create check-in data for last 30 days
    check_in_data = []
    for emp in employees:
        for days_ago in range(30):
            date = datetime.now() - timedelta(days=days_ago)
            check_in_data.append({
                'employee_id': emp['id'],
                'date': date.date(),
                'stress': random.randint(1, 10),
                'energy': random.randint(1, 10),
                'motivation': random.randint(1, 10),
                'work_enjoyment': random.randint(1, 10),
                'notes': random.choice(["", fake.sentence(), ""])
            })
    
    # Create performance data
    performance_data = []
    for emp in employees:
        for month in range(1, 13):
            performance_data.append({
                'employee_id': emp['id'],
                'month': month,
                'kpi': random.randint(60, 100),
                'projects_completed': random.randint(1, 5),
                'feedback_score': random.randint(3, 5),
                'overtime_hours': random.randint(0, 30)
            })
    
    return {
        'employees': pd.DataFrame(employees),
        'check_ins': pd.DataFrame(check_in_data),
        'performance': pd.DataFrame(performance_data)
    }

# Load dummy data
data = generate_dummy_data()
employees_df = data['employees']
check_ins_df = data['check_ins']
performance_df = data['performance']

# Calculate derived metrics
def calculate_metrics(employee_id=None, department=None):
    if employee_id:
        emp_check_ins = check_ins_df[check_ins_df['employee_id'] == employee_id]
        emp_performance = performance_df[performance_df['employee_id'] == employee_id]
    elif department:
        emp_ids = employees_df[employees_df['department'] == department]['id'].tolist()
        emp_check_ins = check_ins_df[check_ins_df['employee_id'].isin(emp_ids)]
        emp_performance = performance_df[performance_df['employee_id'].isin(emp_ids)]
    else:
        emp_check_ins = check_ins_df
        emp_performance = performance_df
    
    # Calculate weekly averages
    latest_date = emp_check_ins['date'].max()
    week_ago = latest_date - timedelta(days=7)
    month_ago = latest_date - timedelta(days=30)
    
    weekly_check_ins = emp_check_ins[emp_check_ins['date'] >= week_ago]
    monthly_check_ins = emp_check_ins[emp_check_ins['date'] >= month_ago]
    
    weekly_avg = weekly_check_ins[['stress', 'energy', 'motivation', 'work_enjoyment']].mean()
    monthly_avg = monthly_check_ins[['stress', 'energy', 'motivation', 'work_enjoyment']].mean()
    
    # Calculate burnout risk
    burnout_risk = "Low"
    if weekly_avg['stress'] > 7 or weekly_avg['energy'] < 4:
        burnout_risk = "High"
    elif weekly_avg['stress'] > 5 or weekly_avg['energy'] < 5:
        burnout_risk = "Moderate"
    
    # Performance metrics
    latest_performance = emp_performance[emp_performance['month'] == datetime.now().month]
    avg_kpi = latest_performance['kpi'].mean()
    
    return {
        'weekly_avg': weekly_avg,
        'monthly_avg': monthly_avg,
        'burnout_risk': burnout_risk,
        'avg_kpi': avg_kpi,
        'latest_date': latest_date
    }

# Dashboard Home View
def show_dashboard(employee_id=None, is_manager=False):
    metrics = calculate_metrics(employee_id)
    
    st.title("Employee Wellness Dashboard")
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Performance Score (This Week)", f"{metrics['weekly_avg']['work_enjoyment']*10:.1f}", 
                 f"{(metrics['weekly_avg']['work_enjoyment'] - metrics['monthly_avg']['work_enjoyment']):.1f} from monthly")
    with col2:
        # Mood tracker summary
        mood_score = (metrics['weekly_avg']['energy'] + metrics['weekly_avg']['motivation']) / 2
        if mood_score > 7:
            mood_emoji = "😊"
        elif mood_score > 5:
            mood_emoji = "😐"
        else:
            mood_emoji = "😞"
        st.metric("Mood Tracker Summary", mood_emoji)
    with col3:
        # Burnout risk indicator
        if metrics['burnout_risk'] == "High":
            st.error("Burnout Risk: 🔴 High")
        elif metrics['burnout_risk'] == "Moderate":
            st.warning("Burnout Risk: 🟡 Moderate")
        else:
            st.success("Burnout Risk: 🟢 Low")
    with col4:
        st.metric("Current KPI Score", f"{metrics['avg_kpi']:.1f}")
    
    # Quick action cards
    st.subheader("Quick Actions")
    action_cols = st.columns(3)
    with action_cols[0]:
        with st.container(border=True):
            st.write("📝 Check-in Today")
            if st.button("Complete Daily Check-In"):
                st.session_state.current_page = "check_in"
                st.rerun()
    with action_cols[1]:
        with st.container(border=True):
            st.write("🤖 AI Suggests Break")
            if st.button("View Suggestions"):
                st.session_state.current_page = "ai_insights"
                st.rerun()
    with action_cols[2]:
        with st.container(border=True):
            st.write("💰 Bonus Potential View")
            if st.button("View Projection"):
                st.session_state.current_page = "compensation"
                st.rerun()
    
    # Mood-Performance Correlation Graph
    st.subheader("Mood-Performance Correlation")
    
    if employee_id:
        # Individual view
        emp_check_ins = check_ins_df[check_ins_df['employee_id'] == employee_id]
        emp_performance = performance_df[performance_df['employee_id'] == employee_id]
        
        # Merge data by month
        emp_check_ins['month'] = pd.to_datetime(emp_check_ins['date']).dt.month
        monthly_mood = emp_check_ins.groupby('month')[['stress', 'energy', 'motivation', 'work_enjoyment']].mean().reset_index()
        merged_data = pd.merge(monthly_mood, emp_performance, on='month')
        
        fig = go.Figure()
        
        # Add KPI line
        fig.add_trace(go.Scatter(
            x=merged_data['month'],
            y=merged_data['kpi'],
            name="Performance KPI",
            line=dict(color='royalblue', width=2)
        ))
        
        # Add mood score (work_enjoyment) line
        fig.add_trace(go.Scatter(
            x=merged_data['month'],
            y=merged_data['work_enjoyment']*10,
            name="Work Enjoyment (Mood)",
            line=dict(color='green', width=2),
            yaxis="y2"
        ))
        
        # Add annotations
        max_kpi_month = merged_data.loc[merged_data['kpi'].idxmax(), 'month']
        fig.add_annotation(
            x=max_kpi_month,
            y=merged_data.loc[merged_data['month'] == max_kpi_month, 'kpi'].values[0],
            text="Peak performance",
            showarrow=True,
            arrowhead=1
        )
        
        fig.update_layout(
            title="Your Monthly Performance vs Mood",
            xaxis_title="Month",
            yaxis_title="Performance KPI",
            yaxis2=dict(
                title="Mood Score",
                overlaying="y",
                side="right",
                range=[0, 10]
            ),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        # Team view
        dept = st.selectbox("Select Department", employees_df['department'].unique())
        dept_metrics = calculate_metrics(department=dept)
        
        dept_check_ins = check_ins_df[check_ins_df['employee_id'].isin(
            employees_df[employees_df['department'] == dept]['id'].tolist()
        )]
        dept_performance = performance_df[performance_df['employee_id'].isin(
            employees_df[employees_df['department'] == dept]['id'].tolist()
        )]
        
        # Group by week
        dept_check_ins['week'] = pd.to_datetime(dept_check_ins['date']).dt.isocalendar().week
        weekly_mood = dept_check_ins.groupby('week')[['stress', 'energy', 'motivation', 'work_enjoyment']].mean().reset_index()
        weekly_performance = dept_performance.groupby('month')[['kpi']].mean().reset_index()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=weekly_mood['week'],
            y=weekly_mood['work_enjoyment']*10,
            name="Team Mood (Work Enjoyment)",
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=weekly_performance['month'],
            y=weekly_performance['kpi'],
            name="Team Performance KPI",
            line=dict(color='royalblue', width=2)
        ))
        
        fig.update_layout(
            title=f"{dept} Team Performance vs Mood",
            xaxis_title="Week/Month",
            yaxis_title="Score",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent check-ins
    if employee_id:
        st.subheader("Your Recent Check-ins")
        recent_check_ins = emp_check_ins.sort_values('date', ascending=False).head(5)
        st.dataframe(recent_check_ins[['date', 'stress', 'energy', 'motivation', 'work_enjoyment', 'notes']], 
                    hide_index=True)
    elif is_manager:
        st.subheader("Team Burnout Risk Overview")
        team_status = []
        for emp_id in employees_df[employees_df['department'] == dept]['id']:
            emp_metrics = calculate_metrics(emp_id)
            emp_name = employees_df[employees_df['id'] == emp_id]['name'].values[0]
            team_status.append({
                'Employee': emp_name,
                'Burnout Risk': emp_metrics['burnout_risk'],
                'Last Check-in': emp_metrics['latest_date'],
                'Performance': emp_metrics['avg_kpi']
            })
        
        team_df = pd.DataFrame(team_status)
        
        # Color coding
        def color_burnout(val):
            if val == "High":
                color = 'red'
            elif val == "Moderate":
                color = 'orange'
            else:
                color = 'green'
            return f'background-color: {color}'
        
        st.dataframe(team_df.style.applymap(color_burnout, subset=['Burnout Risk']), 
                    hide_index=True, use_container_width=True)

# Daily/Weekly Check-In Page
def show_check_in():
    st.title("Daily Check-In")
    
    with st.form("check_in_form"):
        st.subheader("How are you feeling today?")
        
        stress = st.slider("Stress Level", 1, 10, 5)
        energy = st.slider("Energy Level", 1, 10, 5)
        motivation = st.slider("Motivation Level", 1, 10, 5)
        work_enjoyment = st.slider("Work Enjoyment", 1, 10, 5)
        
        notes = st.text_area("Optional Notes", placeholder="What affected your energy today?")
        
        submitted = st.form_submit_button("Submit Check-In")
        
        if submitted:
            # In a real app, this would save to a database
            st.success("Check-in submitted successfully!")
            st.balloons()
            
            # Add some delay before redirecting
            import time
            time.sleep(2)
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    # Show historical data
    if 'current_employee_id' in st.session_state:
        emp_id = st.session_state.current_employee_id
        emp_check_ins = check_ins_df[check_ins_df['employee_id'] == emp_id].sort_values('date', ascending=False).head(7)
        
        st.subheader("Your Recent Check-ins")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=emp_check_ins['date'],
            y=emp_check_ins['stress'],
            name="Stress",
            line=dict(color='red', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=emp_check_ins['date'],
            y=emp_check_ins['energy'],
            name="Energy",
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=emp_check_ins['date'],
            y=emp_check_ins['motivation'],
            name="Motivation",
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title="Your Wellness Trends (Last 7 Days)",
            xaxis_title="Date",
            yaxis_title="Score",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# AI Insights & Alerts Center
def show_ai_insights():
    st.title("AI Insights & Alerts")
    
    # Generate some random insights
    insights = [
        "You might be approaching fatigue. Schedule a break?",
        "Your energy levels tend to drop on Fridays. Consider lighter tasks.",
        "Your performance peaks in the morning. Schedule important work then.",
        "You haven't taken a break in 5 days. Consider a short walk.",
        "Your stress levels are 20% higher than your team average."
    ]
    
    alerts = [
        "Your wellness score dipped after working 7 days straight.",
        "You've been reporting high stress for 3 consecutive days.",
        "Your motivation score is below your typical range."
    ]
    
    # Display as cards
    st.subheader("Your Personalized Insights")
    
    for insight in random.sample(insights, 3):
        with st.container(border=True):
            st.markdown(f"💡 **Insight**  \n{insight}")
    
    st.subheader("Alerts")
    
    for alert in random.sample(alerts, 2):
        with st.container(border=True):
            st.markdown(f"⚠️ **Alert**  \n{alert}")
    
    # Suggestions
    st.subheader("Recommended Actions")
    
    suggestions = [
        "Take a 15-minute walk outside",
        "Schedule a 1:1 with your manager",
        "Try a mindfulness exercise",
        "Consider blocking focus time on your calendar",
        "Attend the upcoming wellness workshop"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(random.sample(suggestions, 4)):
        with cols[i%2]:
            with st.container(border=True):
                st.markdown(f"✅ **Suggestion {i+1}**  \n{suggestion}")
                if st.button("Mark as completed", key=f"suggestion_{i}"):
                    st.success("Great job taking care of yourself!")
    
    # Manager view
    if st.session_state.get('is_manager', False):
        st.subheader("Team Alerts (Manager View)")
        
        team_alerts = [
            "Top performer showing early burnout indicators.",
            "3 team members haven't checked in this week.",
            "Stress levels are 15% higher than company average.",
            "Productivity drops significantly after 3pm."
        ]
        
        for alert in random.sample(team_alerts, 2):
            with st.container(border=True):
                st.markdown(f"🔔 **Team Alert**  \n{alert}")
                st.button("Take Action", key=f"alert_{alert[:10]}")

# Smart Compensation Preview
def show_compensation():
    st.title("Smart Compensation Preview")
    
    # Generate some dummy compensation data
    base_salary = random.randint(80000, 120000)
    performance_bonus = random.randint(5000, 20000)
    wellbeing_bonus = random.randint(1000, 5000)
    total_comp = base_salary + performance_bonus + wellbeing_bonus
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Base Salary", f"${base_salary:,}")
    with col2:
        st.metric("Performance Bonus", f"${performance_bonus:,}")
    with col3:
        st.metric("Wellbeing Bonus", f"${wellbeing_bonus:,}")
    
    st.divider()
    
    # Breakdown chart
    st.subheader("Compensation Breakdown")
    
    breakdown_data = {
        'Component': ['Performance KPIs', 'Feedback Quality', 'Wellbeing Balance'],
        'Percentage': [70, 20, 10],
        'Amount': [
            performance_bonus * 0.7,
            performance_bonus * 0.2,
            wellbeing_bonus
        ]
    }
    
    fig = px.pie(breakdown_data, values='Amount', names='Component',
                 title="Bonus Composition",
                 hover_data=['Percentage'])
    
    st.plotly_chart(fig, use_container_width=True)
    
    # What-if simulator
    st.subheader("What-if Simulator")
    
    with st.expander("Explore different scenarios"):
        burnout_days = st.slider("Days of burnout symptoms", 0, 30, 5)
        productivity_loss = st.slider("Estimated productivity loss (%)", 0, 50, 15)
        
        impact_on_bonus = (performance_bonus * (productivity_loss / 100)) + \
                         (wellbeing_bonus * (burnout_days / 30))
        
        st.metric("Potential Bonus Impact", 
                 f"-${impact_on_bonus:,.0f}",
                 f"{impact_on_bonus/total_comp*100:.1f}% of total compensation")
        
        # Show trajectory
        months = list(range(1, 13))
        current_kpi = random.randint(75, 90)
        
        if burnout_days > 10:
            projected_kpi = [max(50, current_kpi - (i * productivity_loss / 10)) for i in range(12)]
        else:
            projected_kpi = [current_kpi - (i * productivity_loss / 20) for i in range(12)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=projected_kpi,
            name="Projected KPI",
            line=dict(color='red', width=2)
        ))
        
        fig.add_hline(y=current_kpi, line_dash="dot", 
                     annotation_text="Current KPI", 
                     annotation_position="bottom right")
        
        fig.update_layout(
            title="Projected Performance Impact",
            xaxis_title="Months",
            yaxis_title="KPI Score",
            yaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Engagement Toolkit
def show_engagement_toolkit():
    st.title("Engagement Toolkit")
    
    # Personalized suggestions
    st.subheader("Personalized Suggestions")
    
    suggestions = [
        {
            "title": "Attend Mental Wellness Day",
            "description": "Join our quarterly mental wellness workshop to learn stress management techniques.",
            "date": "Next Thursday at 2pm"
        },
        {
            "title": "Role-Switch Opportunity",
            "description": "Your stress indicators match others who benefited from temporary role rotations.",
            "date": "Apply by end of month"
        },
        {
            "title": "Peer Mentoring Program",
            "description": "Based on your skills, you'd be a great mentor for new team members.",
            "date": "Ongoing"
        }
    ]
    
    for suggestion in suggestions:
        with st.container(border=True):
            st.markdown(f"#### {suggestion['title']}")
            st.write(suggestion['description'])
            st.caption(f"⏰ {suggestion['date']}")
            cols = st.columns([1,1,2])
            with cols[0]:
                st.button("Interested", key=f"interest_{suggestion['title'][:5]}")
            with cols[1]:
                st.button("Not Now", key=f"notnow_{suggestion['title'][:5]}")
    
    # Peer connection prompt
    st.subheader("Peer Connection")
    
    peers = random.sample(employees_df['name'].tolist(), 3)
    
    with st.container(border=True):
        st.markdown("#### Connect with Colleagues")
        st.write("Building relationships with colleagues can improve job satisfaction.")
        
        for peer in peers:
            cols = st.columns([3,1])
            with cols[0]:
                st.write(f"👋 {peer}")
            with cols[1]:
                st.button("Schedule Chat", key=f"chat_{peer[:5]}")
    
    # Journal space
    st.subheader("Reflective Journal")
    
    journal_entry = st.text_area("Take a moment to reflect on your week:", 
                               height=150,
                               placeholder="What went well? What challenges did you face?")
    
    if st.button("Save Journal Entry"):
        st.success("Entry saved. Reflection is an important part of growth!")

# Manager View
def show_manager_view():
    st.title("Team Management Dashboard")
    
    # Department selector
    dept = st.selectbox("Select Department", employees_df['department'].unique())
    
    # Team overview
    st.subheader("Team Overview")
    
    # Calculate metrics for each team member
    team_members = employees_df[employees_df['department'] == dept]
    team_data = []
    
    for _, emp in team_members.iterrows():
        metrics = calculate_metrics(emp['id'])
        team_data.append({
            'Name': emp['name'],
            'Role': emp['role'],
            'Burnout Risk': metrics['burnout_risk'],
            'Performance': metrics['avg_kpi'],
            'Last Check-in': metrics['latest_date'],
            'ID': emp['id']
        })
    
    team_df = pd.DataFrame(team_data)
    
    # Color coding function
    def color_burnout(val):
        if val == "High":
            color = 'red'
        elif val == "Moderate":
            color = 'orange'
        else:
            color = 'green'
        return f'background-color: {color}'
    
    # Display team status
    st.dataframe(
        team_df.style.applymap(color_burnout, subset=['Burnout Risk']),
        column_config={
            "ID": None,
            "Performance": st.column_config.ProgressColumn(
                "Performance",
                help="Employee's performance KPI",
                format="%.1f",
                min_value=0,
                max_value=100
            )
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Team analytics
    st.subheader("Team Analytics")
    
    cols = st.columns(2)
    
    with cols[0]:
        # Burnout risk distribution
        burnout_dist = team_df['Burnout Risk'].value_counts().reset_index()
        fig = px.pie(burnout_dist, values='count', names='Burnout Risk',
                     title="Burnout Risk Distribution",
                     color='Burnout Risk',
                     color_discrete_map={'High':'red', 'Moderate':'orange', 'Low':'green'})
        st.plotly_chart(fig, use_container_width=True)
    
    with cols[1]:
        # Performance vs burnout scatter
        fig = px.scatter(team_df, x='Performance', y='Burnout Risk',
                         color='Burnout Risk',
                         color_discrete_map={'High':'red', 'Moderate':'orange', 'Low':'green'},
                         title="Performance vs Burnout Risk",
                         hover_data=['Name', 'Role'])
        st.plotly_chart(fig, use_container_width=True)
    
    # Action buttons
    st.subheader("Team Actions")
    
    action_cols = st.columns(3)
    
    with action_cols[0]:
        with st.container(border=True):
            st.write("📢 Send Check-In Prompt")
            if st.button("Prompt All Team Members"):
                st.success("Check-in prompts sent to all team members!")
    
    with action_cols[1]:
        with st.container(border=True):
            st.write("⚖️ Adjust Workload")
            selected_emp = st.selectbox("Select Employee", team_df['Name'])
            adjustment = st.slider("Workload Adjustment", -50, 50, 0, format="%d%%")
            if st.button("Apply Adjustment"):
                st.success(f"Workload for {selected_emp} adjusted by {adjustment}%")
    
    with action_cols[2]:
        with st.container(border=True):
            st.write("🏆 Offer Recognition")
            selected_emp = st.selectbox("Select Employee to Recognize", team_df['Name'])
            recognition_type = st.selectbox("Recognition Type", 
                                          ["Spot Bonus", "Public Praise", "Development Opportunity"])
            if st.button("Give Recognition"):
                st.success(f"{recognition_type} given to {selected_emp}")

# Login page
def show_login():
    st.title("Employee Wellness Portal")
    
    with st.container(border=True):
        st.subheader("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Simple authentication for demo
            if email.endswith('@company.com') and password == "password":
                # Find employee in our dummy data
                emp = employees_df[employees_df['email'] == email]
                if not emp.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_employee_id = emp['id'].values[0]
                    st.session_state.current_employee_name = emp['name'].values[0]
                    st.session_state.is_manager = emp['manager'].values[0]
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Employee not found in records")
            else:
                st.error("Invalid credentials. Try email ending with @company.com and password 'password'")

# Main app logic
def main():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        show_login()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.current_employee_name}")
        
        if st.session_state.is_manager:
            st.write("👔 Manager View")
        
        st.divider()
        
        if st.button("🏠 Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        if st.button("📝 Daily Check-In"):
            st.session_state.current_page = "check_in"
            st.rerun()
        
        if st.button("🤖 AI Insights"):
            st.session_state.current_page = "ai_insights"
            st.rerun()
        
        if st.button("💰 Compensation"):
            st.session_state.current_page = "compensation"
            st.rerun()
        
        if st.button("🧰 Engagement Toolkit"):
            st.session_state.current_page = "engagement"
            st.rerun()
        
        if st.session_state.is_manager and st.button("👔 Manager View"):
            st.session_state.current_page = "manager"
            st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Page routing
    if st.session_state.current_page == "dashboard":
        show_dashboard(st.session_state.current_employee_id, st.session_state.is_manager)
    elif st.session_state.current_page == "check_in":
        show_check_in()
    elif st.session_state.current_page == "ai_insights":
        show_ai_insights()
    elif st.session_state.current_page == "compensation":
        show_compensation()
    elif st.session_state.current_page == "engagement":
        show_engagement_toolkit()
    elif st.session_state.current_page == "manager":
        show_manager_view()

if __name__ == "__main__":
    main()
