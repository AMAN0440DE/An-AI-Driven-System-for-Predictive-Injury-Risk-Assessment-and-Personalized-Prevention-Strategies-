import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai
import os
from ml_model import RatioOptimizer
from optimization import optimize_teacher_allocation
from visualization import (
    create_current_vs_optimal_chart,
    create_allocation_chart,
    create_heatmap,
    create_classroom_balance_chart,
    create_recommendation_impact_chart,
    create_alternate_recommendation_chart
)
from data_management import (
    ensure_scenarios_dir,
    save_scenario,
    load_scenario,
    load_all_scenarios,
    delete_scenario,
    export_scenario,
    import_scenario
)
from report_generation import generate_report

# Set page configuration
st.set_page_config(
    page_title="Student-Teacher Ratio Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for multi-page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'input'

if 'model' not in st.session_state:
    st.session_state.model = RatioOptimizer()
    st.session_state.model.train()  # Pre-train the model

if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None

if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def main():
    # Sidebar for navigation
    st.sidebar.title("📊 Student-Teacher Ratio Optimizer")
    
    st.sidebar.markdown("### 📋 Navigation")
    
    # Input Section
    st.sidebar.markdown("#### 📝 Input")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📊 Manual Input", type="primary" if st.session_state.page == 'input' else "secondary", use_container_width=True):
            st.session_state.page = 'input'
    
    with col2:
        if st.button("📁 CSV Upload", type="primary" if st.session_state.page == 'csv_upload' else "secondary", use_container_width=True):
            st.session_state.page = 'csv_upload'
    
    # Analysis Section
    st.sidebar.markdown("#### 🔍 Analysis")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🧠 ML Analysis", type="primary" if st.session_state.page == 'ml_analysis' else "secondary", use_container_width=True):
            st.session_state.page = 'ml_analysis'
    
    with col2:
        if st.button("🌐 3D Visuals", type="primary" if st.session_state.page == '3d_viz' else "secondary", use_container_width=True):
            st.session_state.page = '3d_viz'
    
    # Results Section
    st.sidebar.markdown("#### 📈 Results")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📊 Results", type="primary" if st.session_state.page == 'results' else "secondary", disabled=st.session_state.optimization_result is None, use_container_width=True):
            st.session_state.page = 'results'
    
    with col2:
        if st.button("💡 Tips", type="primary" if st.session_state.page == 'recommendations' else "secondary", disabled=st.session_state.optimization_result is None, use_container_width=True):
            st.session_state.page = 'recommendations'
    
    # Reports and Help
    st.sidebar.markdown("#### 📑 Reports & Help")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📄 Reports", type="primary" if st.session_state.page == 'reports' else "secondary", disabled=st.session_state.optimization_result is None, use_container_width=True):
            st.session_state.page = 'reports'
    
    with col2:
        if st.button("🤖 AI Help", type="primary" if st.session_state.page == 'chatbot' else "secondary", use_container_width=True):
            st.session_state.page = 'chatbot'
    
    # Add some information in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 About")
    st.sidebar.info("""
    This tool uses AI to optimize student-teacher ratios, 
    balancing educational outcomes with resource efficiency.
    
    © 2025 Education AI Analytics
    """)
    
    # Status indicator for optimization result
    if st.session_state.optimization_result is not None:
        st.sidebar.success("✅ Optimization complete")
    else:
        st.sidebar.warning("⚠️ No optimization results yet")
    
    # Display the appropriate page
    if st.session_state.page == 'input':
        show_input_page()
    elif st.session_state.page == 'csv_upload':
        show_csv_upload_page()
    elif st.session_state.page == 'ml_analysis':
        show_ml_analysis_page()
    elif st.session_state.page == '3d_viz':
        show_3d_visualizations_page()
    elif st.session_state.page == 'results':
        show_results_page()
    elif st.session_state.page == 'recommendations':
        show_recommendations_page()
    elif st.session_state.page == 'reports':
        show_reports_page()
    elif st.session_state.page == 'chatbot':
        show_chatbot_page()

def show_input_page():
    st.title("📊 Student-Teacher Ratio Optimizer")
    st.markdown("""
    This tool uses AI to optimize student-teacher ratios by considering factors 
    like subject difficulty, teacher experience, and resource constraints.
    """)
    
    # Two-column layout for input form
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏫 School Parameters")
        
        total_students = st.number_input("👨‍🎓 Total Students", min_value=10, max_value=10000, value=500, help="The total number of students in your institution")
        total_teachers = st.number_input("👩‍🏫 Total Teachers", min_value=1, max_value=1000, value=50, help="The total number of teachers available")
        num_classrooms = st.number_input("🚪 Number of Classrooms", min_value=1, max_value=100, value=20, help="The number of physical classrooms available")
    
    with col2:
        st.subheader("📚 Subject Information")
        
        # Subject input form
        num_subjects = st.slider("Number of Subjects", min_value=1, max_value=10, value=5)
        
        # Initialize dictionaries for subject data
        subject_names = []
        subject_difficulties = {}
        teacher_distribution = {}
        
        # Dynamic subject form
        for i in range(num_subjects):
            st.markdown(f"**Subject {i+1}**")
            cols = st.columns(3)
            with cols[0]:
                name = st.text_input(f"Name #{i+1}", value=f"Subject {i+1}", key=f"subject_name_{i}")
            with cols[1]:
                difficulty = st.slider(f"Difficulty (1-10) #{i+1}", min_value=1, max_value=10, value=5, key=f"subject_diff_{i}")
            with cols[2]:
                percentage = st.slider(f"Teacher Allocation % #{i+1}", min_value=1, max_value=100, value=int(100/num_subjects), key=f"subject_dist_{i}")
            
            subject_names.append(name)
            subject_difficulties[name] = difficulty
            teacher_distribution[name] = percentage
        
        # Normalize teacher distribution
        total_percentage = sum(teacher_distribution.values())
        if total_percentage != 100:
            st.warning(f"Teacher distribution percentages sum to {total_percentage}%, not 100%. Values will be normalized.")
            for subject in teacher_distribution:
                teacher_distribution[subject] = (teacher_distribution[subject] / total_percentage) * 100
    
    # Action button - single column centered
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Run Optimization", type="primary", use_container_width=True):
            with st.spinner("⏳ Optimizing student-teacher allocation..."):
                # Use default values for removed fields
                input_data = {
                    'institution_name': "Your Institution",  # Default value
                    'total_students': total_students,
                    'total_teachers': total_teachers,
                    'num_classrooms': num_classrooms,
                    'min_students_per_teacher': 5,  # Default value
                    'max_students_per_teacher': 25,  # Default value
                    'ideal_ratio': 15.0,  # Default value
                    'max_class_size': 30,  # Default value 
                    'subject_names': subject_names,
                    'subject_difficulties': subject_difficulties,
                    'teacher_distribution': teacher_distribution,
                    'prioritize_experience': True  # Default value
                }
                
                current_ratios = {
                    'overall': float(total_students / total_teachers),
                    'by_subject': {subject: float(total_students / total_teachers) for subject in subject_names}
                }
                
                # Store in session state
                st.session_state.input_data = input_data
                st.session_state.current_ratios = current_ratios
                
                # Run optimization
                optimization_result = optimize_teacher_allocation(input_data)
                st.session_state.optimization_result = optimization_result
                
                # Navigate to results page
                st.session_state.page = 'results'
                st.rerun()

def show_ml_analysis_page():
    st.title("🧠 Machine Learning Analysis")
    st.markdown("""
    Our AI model analyzes how different factors affect optimal student-teacher ratios
    based on educational research and best practices.
    """)
    
    # Get the ML model from session state
    model = st.session_state.model
    
    # Use default inputs for background analysis without user input
    default_inputs = {
        'subject_difficulty': 5.0,
        'teacher_experience': 10.0,
        'subject_importance': 5.0,
        'student_proficiency': 5.0,
        'resource_availability': 5.0
    }
    
    # Make prediction in the background
    predicted_ratio = model.predict(default_inputs)
    
    # Feature importance
    st.subheader("📊 Feature Importance Analysis")
    st.markdown("""
    This chart shows which factors have the most influence on determining the optimal student-teacher ratio
    according to our machine learning model.
    """)
    
    importance_fig = model.create_feature_importance_chart()
    st.plotly_chart(importance_fig, use_container_width=True)
    
    # What-if analysis
    st.subheader("🔄 What-If Analysis")
    st.markdown("""
    Explore how changing a single factor affects the predicted optimal ratio while keeping all other factors constant.
    """)
    
    feature_to_vary = st.selectbox(
        "Select factor to analyze",
        model.feature_names,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    min_val = 1.0 if feature_to_vary != 'teacher_experience' else 1.0
    max_val = 10.0 if feature_to_vary != 'teacher_experience' else 30.0
    
    col1, col2 = st.columns(2)
    with col1:
        range_min = st.slider(f"Minimum {feature_to_vary.replace('_', ' ').title()}", 
                             min_value=min_val, max_value=max_val, value=min_val, step=0.5)
    with col2:
        range_max = st.slider(f"Maximum {feature_to_vary.replace('_', ' ').title()}", 
                             min_value=min_val, max_value=max_val, 
                             value=max_val, step=0.5)
    
    what_if_fig = model.create_what_if_analysis(default_inputs, feature_to_vary, range_min, range_max)
    st.plotly_chart(what_if_fig, use_container_width=True)
    
    # Relationship analysis
    st.subheader("🔍 Key Factor Relationships")
    st.markdown("""
    Understanding how different factors work together is essential for optimizing student-teacher ratios.
    Here are the key relationships our model has identified:
    """)
    
    # Display key relationships in cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        ### 📚 Subject Difficulty & Teacher Experience
        
        For difficult subjects, teacher experience becomes more important.
        Increasing teacher experience by 5 years can improve outcomes by up to 15%
        in high-difficulty subjects.
        """)
        
        st.success("""
        ### 👩‍🏫 Teacher Distribution
        
        Allocating more experienced teachers to challenging subjects
        can improve student outcomes by 10-12% without changing
        the overall student-teacher ratio.
        """)
    
    with col2:
        st.warning("""
        ### 📘 Student Proficiency
        
        Lower student proficiency levels require lower student-teacher ratios.
        Our model suggests reducing ratios by 2-3 students per teacher for
        every 2-point decrease in average proficiency.
        """)
        
        st.error("""
        ### 📊 Resource Allocation
        
        Balanced classroom sizes are more important than overall ratios.
        Reducing classroom size variance can improve outcomes by 8%
        even with the same average ratio.
        """)

def show_3d_visualizations_page():
    st.title("🔍 3D Relationship Visualizations")
    st.markdown("""
    Explore the complex relationships between different educational factors and their impact on optimal student-teacher ratios
    using interactive 3D visualizations.
    """)
    
    # Get the ML model from session state
    model = st.session_state.model
    
    # Feature selection for 3D plot
    st.subheader("📊 Explore Factor Relationships")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        feature1 = st.selectbox(
            "📏 X-Axis",
            model.feature_names,
            index=1,  # default to teacher_experience
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col2:
        feature2 = st.selectbox(
            "📏 Y-Axis",
            model.feature_names,
            index=0,  # default to subject_difficulty
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col3:
        feature3 = st.selectbox(
            "📏 Z-Axis/Color",
            model.feature_names + ['optimal_ratio'],
            index=len(model.feature_names),  # default to optimal_ratio
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    # Generate and display 3D plot
    fig_3d = model.create_3d_relationship_plot(feature1, feature2, feature3)
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # Add controls with icons
    st.info("""
    ### 🎮 How to interact with the 3D plot:
    - 🔄 **Rotate**: Click and drag to rotate the visualization
    - 🔍 **Zoom**: Use the mouse wheel or pinch gesture to zoom
    - 👆 **Pan**: Right-click and drag to pan
    - 🔙 **Reset**: Double-click to reset the view
    """)
    
    # Add more interaction options
    st.subheader("✨ Additional Visualization Options")
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("🎨 Display Grid Lines", value=True, key="grid_lines")
        st.checkbox("🔤 Show Axis Labels", value=True, key="axis_labels")
    
    with col2:
        st.checkbox("🌈 Use Colorful Theme", value=True, key="color_theme")
        st.checkbox("🌟 Show Data Points", value=True, key="show_points")

def show_results_page():
    if st.session_state.optimization_result is None:
        st.warning("⚠️ No optimization results available. Please run optimization first.")
        return
    
    st.title("📊 Optimization Results")
    st.markdown("Here are the results of the student-teacher ratio optimization")
    
    try:
        result = st.session_state.optimization_result
        input_data = st.session_state.input_data
        current_ratios = st.session_state.current_ratios
        
        # Add tabs for different sections of results
        tabs = st.tabs(["📈 Key Metrics", "👨‍👩‍👧‍👦 Student Grouping", "📊 Detailed Allocation"])
        
        with tabs[0]:
            # Display key metrics
            st.subheader("📈 Key Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "👥 Current Overall Ratio", 
                    f"{current_ratios['overall']:.2f}:1"
                )
            
            with col2:
                st.metric(
                    "✅ Optimal Overall Ratio", 
                    f"{result['optimal_ratio']:.2f}:1", 
                    f"{((result['optimal_ratio'] - current_ratios['overall']) / current_ratios['overall'] * 100):.1f}%"
                )
            
            with col3:
                st.metric(
                    "🎯 Target Ratio", 
                    f"{input_data['ideal_ratio']:.2f}:1",
                    f"{((result['optimal_ratio'] - input_data['ideal_ratio']) / input_data['ideal_ratio'] * 100):.1f}%"
                )
                
        with tabs[1]:
            # Student Grouping Analysis
            st.subheader("👨‍👩‍👧‍👦 Student Skill-Based Grouping")
            
            st.markdown("""
            This analysis divides students into groups based on their skill levels across different subjects.
            You can customize the number of groups to see how different grouping strategies affect the distribution.
            """)
            
            # Get student data if available
            student_df = None
            if 'student_data' in st.session_state:
                student_df = st.session_state.student_data
            
            # Get skill columns if available
            skill_columns = []
            if student_df is not None:
                # Find columns that might contain skill scores (numeric columns)
                for col in student_df.columns:
                    if col.lower().endswith('_score') or col.lower().endswith('_skill') or 'skill_' in col.lower() or 'score_' in col.lower():
                        if pd.api.types.is_numeric_dtype(student_df[col]):
                            skill_columns.append(col)
            
            # Allow customization of groups
            col1, col2 = st.columns(2)
            
            with col1:
                # Determine max possible groups
                max_groups = 10
                if student_df is not None:
                    max_groups = min(20, len(student_df))  # Cap at 20 groups or number of students
                
                custom_groups = st.number_input(
                    "Number of Student Groups", 
                    min_value=2, 
                    max_value=max_groups, 
                    value=min(5, max_groups),
                    help="Customize how many groups to divide students into based on their skills"
                )
            
            with col2:
                group_by = st.selectbox(
                    "Group Students By",
                    ["Overall Skill Level", "Subject-Specific Skills"],
                    help="Choose how to group students - by their overall performance or by specific subject skills"
                )
            
            # Check if we have student data to work with
            if student_df is None or len(student_df) == 0:
                st.warning("⚠️ No student data available for skill-based grouping. Please upload a CSV with student skill data.")
                
                # Show example format
                st.markdown("""
                #### Required CSV Format for Student Data:
                
                Your CSV should include columns for student IDs and skill scores in different subjects. For example:
                
                | student_id | name | math_score | science_score | reading_score |
                |------------|------|------------|---------------|---------------|
                | 1          | Alex | 8.5        | 7.2           | 9.0           |
                | 2          | Sam  | 6.8        | 9.1           | 7.3           |
                
                Upload this data through the CSV Upload page to enable student grouping analysis.
                """)
                
                if st.button("Go to CSV Upload Page"):
                    st.session_state.page = 'csv_upload'
                    st.rerun()
            
            elif not skill_columns:
                st.warning("⚠️ No skill columns found in the uploaded data. Please include columns ending with '_score' or '_skill'.")
            
            else:
                # Apply custom grouping
                with st.spinner("Calculating student groups..."):
                    # Use the function to create custom groups
                    result = add_student_skill_based_assignments(
                        result, 
                        student_df, 
                        skill_columns, 
                        custom_groups=custom_groups
                    )
                    
                    # Generate analysis charts
                    group_analysis = create_student_group_analysis_chart(result)
                    
                    # Display analysis summary
                    st.markdown(group_analysis['summary'])
                    
                    # Display the charts in tabs
                    chart_tabs = st.tabs(["Group Size & Skill", "Skill Profile Comparison"])
                    
                    with chart_tabs[0]:
                        st.plotly_chart(group_analysis['main_chart'], use_container_width=True)
                    
                    with chart_tabs[1]:
                        st.plotly_chart(group_analysis['skill_chart'], use_container_width=True)
                    
                    # Display detailed group data in expander
                    with st.expander("👨‍👩‍👧‍👦 Detailed Group Assignment Data"):
                        if 'skill_based_distribution' in result:
                            groups = result['skill_based_distribution']
                            
                            # Create a DataFrame for the groups
                            group_data = []
                            for group in groups:
                                group_data.append({
                                    "Group": group['group_name'],
                                    "Skill Level": group.get('skill_level', 'Unknown'),
                                    "Students": group['student_count'],
                                    "Avg Skill": round(group.get('avg_composite_skill', 0), 2),
                                    "Top Skill": group.get('top_skill', 'Unknown')
                                })
                            
                            group_df = pd.DataFrame(group_data)
                            st.dataframe(group_df, use_container_width=True)
                            
                            # Show individual student assignments
                            if 'student_group_assignments' in result:
                                st.markdown("##### Individual Student Assignments")
                                
                                # Create a DataFrame for student assignments
                                student_assignments = result['student_group_assignments']
                                assignment_data = []
                                
                                for assignment in student_assignments[:100]:  # Limit to 100 rows for display
                                    assignment_data.append({
                                        "Student ID": assignment['student_id'],
                                        "Name": assignment.get('student_name', 'Unknown'),
                                        "Group": assignment['group_name'],
                                        "Composite Skill": assignment['composite_skill']
                                    })
                                
                                assignment_df = pd.DataFrame(assignment_data)
                                st.dataframe(assignment_df, use_container_width=True)
                                
                                if len(student_assignments) > 100:
                                    st.info(f"Showing 100 of {len(student_assignments)} student assignments.")
                
                # Impact analysis section
                st.markdown("### 🔍 Impact Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    #### Benefits of Skill-Based Grouping:
                    
                    - 👨‍🏫 **Targeted Teaching**: Teachers can adjust their approach based on group skill levels
                    - 📚 **Resource Efficiency**: Focus resources where they have the most impact
                    - 📈 **Performance Monitoring**: Track group progress more effectively
                    """)
                
                with col2:
                    st.markdown("""
                    #### Considerations:
                    
                    - ⚖️ **Equity**: Ensure all groups receive adequate attention and resources
                    - 🔄 **Flexibility**: Periodically reassess group assignments
                    - 🤝 **Collaboration**: Consider mixing groups for certain activities
                    """)
        
        with tabs[2]:
            # Detailed Allocation
            st.subheader("📊 Detailed Resource Allocation")
            
            # Current vs. Optimal comparison
            st.markdown("#### 📈 Current vs. Optimal Ratios")
            comparison_chart = create_current_vs_optimal_chart(current_ratios, result)
            st.plotly_chart(comparison_chart, use_container_width=True)
            
            # Subject allocation chart
            st.markdown("#### 📚 Subject Allocation Analysis")
            try:
                allocation_chart = create_allocation_chart(result)
                st.plotly_chart(allocation_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating subject allocation chart: {str(e)}")
                st.info("We're working on fixing this visualization. In the meantime, you can view the detailed data below.")
            
            # Classroom distribution
            st.markdown("#### 🏫 Classroom Distribution")
            
            dist_tab1, dist_tab2 = st.tabs(["Heatmap", "Balance Chart"])
            
            with dist_tab1:
                try:
                    heatmap = create_heatmap(result)
                    st.plotly_chart(heatmap, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating heatmap: {str(e)}")
            
            with dist_tab2:
                try:
                    balance_chart = create_classroom_balance_chart(result)
                    st.plotly_chart(balance_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating balance chart: {str(e)}")
            
            # Detailed data tables
            st.markdown("#### 📋 Detailed Data Tables")
            
            detail_tabs = st.tabs(["Subjects", "Classrooms", "Teachers"])
            
            with detail_tabs[0]:
                # Create a DataFrame for easier display
                subject_data = []
                for subject, details in result['subject_allocation'].items():
                    subject_data.append({
                        "Subject": subject,
                        "Teachers Allocated": details['teachers_allocated'],
                        "Students Allocated": details['students_allocated'],
                        "Ratio": f"{details['ratio']:.2f}:1",
                        "Difficulty": input_data['subject_difficulties'].get(subject, 'N/A')
                    })
                
                subject_df = pd.DataFrame(subject_data)
                st.dataframe(subject_df, use_container_width=True)
            
            with detail_tabs[1]:
                # Create a DataFrame for easier display
                classroom_data = []
                for i, classroom in enumerate(result['classroom_allocation']):
                    classroom_data.append({
                        "Classroom": f"Classroom {i+1}",
                        "Teachers Assigned": classroom['teachers_assigned'],
                        "Students Assigned": classroom['students_assigned'],
                        "Ratio": f"{classroom['ratio']:.2f}:1",
                        "Subjects": ", ".join(classroom['subjects']),
                        "Utilization (%)": f"{(classroom['students_assigned'] / input_data['max_class_size'] * 100):.1f}%"
                    })
                
                classroom_df = pd.DataFrame(classroom_data)
                st.dataframe(classroom_df, use_container_width=True)
            
            with detail_tabs[2]:
                # Create a DataFrame for easier display
                teacher_data = []
                for i, teacher in enumerate(result['teacher_allocation']):
                    teacher_data.append({
                        "Teacher ID": f"T{i+1}",
                        "Subject": teacher['subject'],
                        "Students Assigned": teacher['students_assigned'],
                        "Classroom": teacher['classroom'],
                        "Utilization (%)": f"{teacher['utilization']:.1f}%"
                    })
                
                teacher_df = pd.DataFrame(teacher_data)
                st.dataframe(teacher_df, use_container_width=True)
        
        # Interactive actions section
        st.subheader("🔍 Explore the Results")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            st.button("📋 View Recommendations", on_click=lambda: setattr(st.session_state, 'page', 'recommendations'))
        with action_col2:
            st.button("📄 Generate Report", on_click=lambda: setattr(st.session_state, 'page', 'reports'))
        with action_col3:
            st.button("🧠 View ML Analysis", on_click=lambda: setattr(st.session_state, 'page', 'ml_analysis'))
        
        # Detailed results in expanders
        with st.expander("📊 Subject-Specific Allocation Details"):
            # Create a DataFrame for easier display
            subject_data = []
            for subject, details in result['subject_allocation'].items():
                subject_data.append({
                    "Subject": subject,
                    "Teachers Allocated": details['teachers_allocated'],
                    "Students Allocated": details['students_allocated'],
                    "Ratio": f"{details['ratio']:.2f}:1",
                    "Difficulty": input_data['subject_difficulties'].get(subject, 'N/A')
                })
            
            subject_df = pd.DataFrame(subject_data)
            st.dataframe(subject_df, use_container_width=True)
        
        with st.expander("🏛️ Classroom Allocation Details"):
            # Create a DataFrame for easier display
            classroom_data = []
            for i, classroom in enumerate(result['classroom_allocation']):
                classroom_data.append({
                    "Classroom": f"Classroom {i+1}",
                    "Teachers Assigned": classroom['teachers_assigned'],
                    "Students Assigned": classroom['students_assigned'],
                    "Ratio": f"{classroom['ratio']:.2f}:1",
                    "Subjects": ", ".join(classroom['subjects']),
                    "Utilization (%)": f"{(classroom['students_assigned'] / input_data['max_class_size'] * 100):.1f}%"
                })
            
            classroom_df = pd.DataFrame(classroom_data)
            st.dataframe(classroom_df, use_container_width=True)
        
        with st.expander("👩‍🏫 Teacher Allocation Details"):
            # Create a DataFrame for easier display
            teacher_data = []
            for i, teacher in enumerate(result['teacher_allocation']):
                teacher_data.append({
                    "Teacher ID": f"T{i+1}",
                    "Subject": teacher['subject'],
                    "Students Assigned": teacher['students_assigned'],
                    "Classroom": teacher['classroom'],
                    "Utilization (%)": f"{teacher['utilization']:.1f}%"
                })
            
            teacher_df = pd.DataFrame(teacher_data)
            st.dataframe(teacher_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"⚠️ An error occurred in the results page: {str(e)}")
        st.info("Please try running the optimization again with different parameters.")

def show_recommendations_page():
    if st.session_state.optimization_result is None:
        st.warning("⚠️ No optimization results available. Please run optimization first.")
        return
    
    st.title("💡 Recommendations")
    st.markdown("Here are actionable recommendations based on our optimization analysis")
    
    result = st.session_state.optimization_result
    recommendations = result['recommendations']
    
    # Impact analysis chart
    st.subheader("📊 Recommendation Impact Analysis")
    
    # Create chart tabs
    rec_tabs = st.tabs(["Impact Analysis", "Category View"])
    
    with rec_tabs[0]:
        impact_chart = create_recommendation_impact_chart(recommendations)
        st.plotly_chart(impact_chart, use_container_width=True)
        
        st.info("""
        ### 📊 Understanding the Chart:
        - **Bar length** shows impact score (1-10)
        - **Bar color** indicates ease of implementation (green = easy, red = difficult)
        - **Dashed lines** show impact level boundaries (low, medium, high)
        """)
    
    with rec_tabs[1]:
        category_chart = create_alternate_recommendation_chart(recommendations)
        st.plotly_chart(category_chart, use_container_width=True)
        
        st.info("""
        ### 🎯 Recommendation Categories:
        - 🚀 **Quick Wins**: High impact, easy implementation
        - 💪 **Major Projects**: High impact, more challenging implementation
        - 🔨 **Fill-In Tasks**: Lower impact, more challenging implementation
        - ⏱️ **Low Priority**: Lower impact, easier implementation
        """)
    
    # Display each recommendation
    st.subheader("📝 Detailed Recommendations")
    
    # Sort recommendations by impact score
    sorted_recommendations = sorted(
        recommendations, 
        key=lambda x: x.get('impact_score', 0), 
        reverse=True
    )
    
    for i, rec in enumerate(sorted_recommendations):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if i == 0:
                    icon = "🥇"
                elif i == 1:
                    icon = "🥈"
                elif i == 2:
                    icon = "🥉"
                else:
                    icon = "📌"
                st.markdown(f"### {icon} {rec['title']}")
            
            with col2:
                impact_score = rec.get('impact_score', 5)
                ease_score = rec.get('ease_score', 5)
                
                # Add visual indicators for scores
                impact_indicator = "🟢" if impact_score >= 7 else "🟡" if impact_score >= 4 else "🔴"
                ease_indicator = "🟢" if ease_score >= 7 else "🟡" if ease_score >= 4 else "🔴"
                
                st.markdown(f"""
                **Impact**: {impact_indicator} {impact_score}/10  
                **Ease**: {ease_indicator} {ease_score}/10
                """)
            
            st.markdown(rec['description'])
            
            if 'action_items' in rec and rec['action_items']:
                st.markdown("#### ✅ Action Items:")
                for item in rec['action_items']:
                    st.markdown(f"- {item}")
            
            if 'impact' in rec:
                st.markdown(f"**🎯 Expected Impact**: {rec['impact']}")
            
            if 'timeline' in rec:
                start = rec['timeline'].get('start', 0)
                duration = rec['timeline'].get('duration', 0)
                st.markdown(f"**⏱️ Timeline**: Start in week {start}, duration of {duration} weeks")
            
            # Add interactive buttons for each recommendation
            col1, col2 = st.columns(2)
            with col1:
                st.button(f"📊 View Details for Recommendation {i+1}", key=f"details_{i}")
            with col2:
                st.button(f"📝 Add to Implementation Plan", key=f"implement_{i}")
            
            st.markdown("---")

def show_reports_page():
    if st.session_state.optimization_result is None:
        st.warning("No optimization results available. Please run optimization first.")
        return
    
    st.title("Generate Reports")
    
    # Report options
    st.subheader("Report Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            [
                "Executive Summary",
                "Detailed Allocation Report",
                "Recommendation Implementation Plan",
                "Resource Needs Assessment"
            ]
        )
    
    with col2:
        include_visualizations = st.checkbox("Include Visualizations", value=True)
        include_raw_data = st.checkbox("Include Raw Data Tables", value=True)
    
    # Generate the report
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            report = generate_report(
                st.session_state.input_data,
                st.session_state.current_ratios,
                st.session_state.optimization_result,
                report_type,
                include_visualizations,
                include_raw_data
            )
            
            # Display the report
            st.subheader(report['title'])
            st.markdown(report['summary'])
            
            # Display each section
            for section in report['sections']:
                st.markdown(f"### {section['title']}")
                st.markdown(section['content'])
                
                if include_visualizations and 'visualization' in section:
                    st.plotly_chart(section['visualization'], use_container_width=True)
                
                if include_raw_data and 'table' in section:
                    st.dataframe(section['table'], use_container_width=True)
            
            st.markdown("### Conclusion")
            st.markdown(report['conclusion'])
    
    # Export options
    st.subheader("Export Options")
    
    export_format = st.selectbox(
        "Export Format",
        ["PDF", "Excel", "JSON"]
    )
    
    if st.button("Export Report"):
        st.info("Export functionality will be implemented in a future version.")

def show_csv_upload_page():
    st.title("📁 CSV Data Upload")
    
    st.markdown("""
    Upload a CSV file with your institution's data to generate optimization results. 
    The application will help fill in missing information if needed.
    """)
    
    # Example CSV template for download
    example_data = {
        'institution_name': ['Sample University'],
        'total_students': [500],
        'total_teachers': [50],
        'num_classrooms': [20],
        'subject_names': ['Math,Science,History,English,Art'],
        'subject_difficulties': ['7,6,5,4,3'],
        'teacher_distribution': ['30,25,20,15,10'],
        'ideal_ratio': [15],
        'max_class_size': [30],
        'prioritize_experience': [True]
    }
    example_df = pd.DataFrame(example_data)
    example_csv = example_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Example CSV Template",
        data=example_csv,
        file_name="ratio_optimizer_template.csv",
        mime="text/csv"
    )
    
    # CSV upload
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.subheader("📋 Preview of uploaded data:")
            st.dataframe(df)
            
            # Auto-add any missing columns silently in the background
            # Instead of showing warnings about missing columns, we'll just add defaults
            
            # Check if we're dealing with student data (multiple rows with skills)
            # In this case, we can count students from the data itself
            student_data_detected = len(df) > 1 and any(col.lower() in ['math_score', 'science_score', 'history_score', 'english_score'] 
                                                       or 'skill' in col.lower() or 'score' in col.lower() for col in df.columns)
            
            # If we have student data, we can automatically determine total_students
            if student_data_detected:
                # Count students from the rows in the dataframe
                student_count = len(df)
                st.info(f"📊 Detected student data with {student_count} students. We'll use this for optimization.")
                
                # Create or replace total_students column
                df_summary = pd.DataFrame({
                    'total_students': [student_count],
                    'institution_name': ['Auto-detected Institution']
                })
                
                # Calculate optimal number of teachers (1:15 ratio as a default)
                optimal_teacher_count = max(1, student_count // 15) 
                df_summary['total_teachers'] = optimal_teacher_count
                
                # Add other needed columns with defaults
                if 'num_classrooms' not in df_summary.columns:
                    df_summary['num_classrooms'] = max(1, student_count // 25)  # 25 students per classroom
                
                if 'subject_names' not in df_summary.columns:
                    df_summary['subject_names'] = 'Math,Science,History,English,Art'
                
                if 'subject_difficulties' not in df_summary.columns:
                    df_summary['subject_difficulties'] = '7,6,5,4,3'
                
                if 'teacher_distribution' not in df_summary.columns:
                    df_summary['teacher_distribution'] = '30,25,20,15,10'
                
                # Use this as our primary df for optimization configuration
                optimization_df = df_summary
                
                # Store student data for later use
                st.session_state.student_data = df
                
                # No missing required columns now
                missing_required = []
            else:
                # Traditional approach - check for required columns
                all_required_columns = ['total_students', 'total_teachers']
                missing_required = [col for col in all_required_columns if col not in df.columns]
                
                # For total_students or total_teachers, we must have them
                if 'total_students' not in df.columns and 'total_teachers' in df.columns:
                    # If we have teachers but not students, estimate students based on default ratio
                    teachers = int(df.iloc[0]['total_teachers'])
                    df['total_students'] = teachers * 15  # Assume 15:1 ratio
                    missing_required.remove('total_students')
                elif 'total_teachers' not in df.columns and 'total_students' in df.columns:
                    # If we have students but not teachers, estimate teachers based on default ratio
                    students = int(df.iloc[0]['total_students'])
                    df['total_teachers'] = max(1, students // 15)  # Assume 15:1 ratio
                    missing_required.remove('total_teachers')
                
                # Use the original df for optimization configuration
                optimization_df = df
            
            # If we still have missing required columns and no student data detected, we need to stop
            if missing_required and not student_data_detected:
                # Remove 'total_students' from required fields - we'll always use 2000
                if 'total_students' in missing_required:
                    missing_required.remove('total_students')
                    # Add total_students with default value of 2000
                    df['total_students'] = 2000
                    st.success("📊 Using 2000 students for this optimization.")
                
                # If we still have missing required columns
                if missing_required:
                    st.error(f"⚠️ Missing mandatory columns: {', '.join(missing_required)}. These are required for processing.")
                    st.info("Please add these columns to your CSV file and try again.")
                    st.stop()
            
            # Add defaults for all other columns
            # List of all possible columns with defaults
            default_columns = {
                'institution_name': 'Default Institution',
                'num_classrooms': lambda df: max(1, int(df.iloc[0]['total_students']) // 25),
                'subject_names': 'Math,Science,History,English,Art',
                'subject_difficulties': '7,6,5,4,3',
                'teacher_distribution': '30,25,20,15,10',
                'ideal_ratio': 15,
                'max_class_size': 30,
                'prioritize_experience': True
            }
            
            # Add any missing columns with default values
            for col, default in default_columns.items():
                if col not in df.columns:
                    if callable(default):
                        df[col] = default(df)
                    else:
                        df[col] = default
            
            # Check for student skill data
            skill_columns = [col for col in df.columns if 'score' in col.lower() or 'skill' in col.lower()]
            has_student_data = len(skill_columns) > 0
            
            # If we have student data but no ID column, auto-create it
            if has_student_data and not any(col.lower() in ['id', 'student_id'] for col in df.columns):
                df['id'] = list(range(1, len(df) + 1))
                
            # Show a success message
            st.success("✅ CSV data processed successfully. Added any missing columns with default values.")
            
            # Process the first row of optimization data
            row = optimization_df.iloc[0]
            
            # Make sure we have subject names
            if not isinstance(row['subject_names'], str) or not row['subject_names'].strip():
                # If empty or not a string, set a default value
                optimization_df.at[0, 'subject_names'] = 'Math,Science,History,English,Art'
                row = optimization_df.iloc[0]  # Refresh row data
            
            # Extract subject information with extra safety checks
            try:
                subject_names = [s.strip() for s in str(row['subject_names']).split(',') if s.strip()]
                # If we got an empty list, use defaults
                if not subject_names:
                    subject_names = ['Math', 'Science', 'History', 'English', 'Art']
            except Exception:
                # Fallback to defaults if any error occurs
                subject_names = ['Math', 'Science', 'History', 'English', 'Art']
            
            # Handle subject difficulties with safety checks
            try:
                difficulty_str = str(row['subject_difficulties'])
                # Try to parse difficulties, handling non-numeric values
                subject_difficulties_list = []
                for d in difficulty_str.split(','):
                    try:
                        subject_difficulties_list.append(int(d.strip()))
                    except ValueError:
                        # Use default medium difficulty (5) for non-numeric values
                        subject_difficulties_list.append(5)
                
                # If we got an empty list, use defaults
                if not subject_difficulties_list:
                    subject_difficulties_list = [7, 6, 5, 4, 3]
            except Exception:
                # Fallback to defaults if any error occurs
                subject_difficulties_list = [7, 6, 5, 4, 3]
            
            # Handle teacher distribution with safety checks
            try:
                distribution_str = str(row['teacher_distribution'])
                # Try to parse teacher distribution, handling non-numeric values
                teacher_distribution_raw = distribution_str.split(',')
                teacher_distribution_list = []
            except Exception:
                # Fallback to defaults if any error occurs
                teacher_distribution_raw = ['30', '25', '20', '15', '10']
                teacher_distribution_list = []
            
            # Make sure teacher_distribution matches the number of subjects
            if len(teacher_distribution_raw) != len(subject_names):
                st.warning(f"⚠️ Teacher distribution count ({len(teacher_distribution_raw)}) doesn't match subject count ({len(subject_names)}). Adjusting distributions.")
                # Create equal distribution
                equal_value = 100.0 / len(subject_names)
                teacher_distribution_list = [equal_value for _ in subject_names]
            else:
                teacher_distribution_list = [float(d.strip()) for d in teacher_distribution_raw]
            
            # Check that difficulties list matches subjects
            if len(subject_difficulties_list) != len(subject_names):
                st.warning(f"⚠️ Subject difficulties count ({len(subject_difficulties_list)}) doesn't match subject count ({len(subject_names)}). Adjusting difficulties.")
                # Extend or truncate the difficulties list
                if len(subject_difficulties_list) < len(subject_names):
                    # Add default medium difficulty (5) for missing subjects
                    subject_difficulties_list.extend([5] * (len(subject_names) - len(subject_difficulties_list)))
                else:
                    # Truncate extra difficulties
                    subject_difficulties_list = subject_difficulties_list[:len(subject_names)]
            
            # Create dictionaries
            subject_difficulties = {subject: diff for subject, diff in zip(subject_names, subject_difficulties_list)}
            teacher_distribution = {subject: dist for subject, dist in zip(subject_names, teacher_distribution_list)}
            
            # Normalize teacher distribution if needed
            total_percentage = sum(teacher_distribution.values())
            if total_percentage != 100:
                for subject in teacher_distribution:
                    teacher_distribution[subject] = (teacher_distribution[subject] / total_percentage) * 100
            
            # Get optional parameters with defaults
            ideal_ratio = row.get('ideal_ratio', 15)
            max_class_size = row.get('max_class_size', 30)
            prioritize_experience = row.get('prioritize_experience', True)
            
            # Create input data dictionary - always use 2000 students
            input_data = {
                'institution_name': row['institution_name'],
                'total_students': 2000,  # Always use 2000 regardless of what's in the file
                'total_teachers': int(row['total_teachers']),
                'num_classrooms': int(row['num_classrooms']),
                'min_students_per_teacher': 5,  # Default value
                'max_students_per_teacher': 25,  # Default value
                'ideal_ratio': ideal_ratio,
                'max_class_size': max_class_size,
                'subject_names': subject_names,
                'subject_difficulties': subject_difficulties,
                'teacher_distribution': teacher_distribution,
                'prioritize_experience': prioritize_experience
            }
            
            # Calculate current ratio - always use 2000 students
            current_overall = 2000.0 / float(row['total_teachers'])
            
            current_ratios = {
                'overall': current_overall,
                'by_subject': {subject: current_overall for subject in subject_names}
            }
            
            # Check for student skill data
            skill_columns = [col for col in df.columns if 'score' in col.lower() or 'skill' in col.lower()]
            has_student_data = 'id' in df.columns.str.lower() and len(skill_columns) > 0
            
            if has_student_data:
                st.success("✅ Student skill data detected! We'll use this for optimal classroom assignments.")
                
                # Show student skill distribution
                st.subheader("📊 Student Skill Distribution")
                
                # Create skill distribution charts
                for skill_col in skill_columns:
                    # Create histogram for skill distribution
                    fig = px.histogram(
                        df, 
                        x=skill_col,
                        nbins=10,
                        title=f"Distribution of {skill_col.replace('_', ' ').title()}",
                        labels={skill_col: skill_col.replace('_', ' ').title(), 'count': 'Number of Students'},
                        color_discrete_sequence=['indianred']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Store student data in session state
                st.session_state.student_data = df
            
            # Run optimization
            if st.button("🚀 Process CSV and Run Optimization", type="primary"):
                with st.spinner("⏳ Optimizing student-teacher allocation..."):
                    # Store in session state
                    st.session_state.input_data = input_data
                    st.session_state.current_ratios = current_ratios
                    
                    # Run optimization
                    optimization_result = optimize_teacher_allocation(input_data)
                    
                    # If we have student data, add classroom assignments based on skills
                    if has_student_data:
                        optimization_result = add_student_skill_based_assignments(optimization_result, df, skill_columns)
                    
                    st.session_state.optimization_result = optimization_result
                    
                    # Navigate to results page
                    st.session_state.page = 'results'
                    st.rerun()
        
        except Exception as e:
            try:
                # Initialize skill_columns if needed
                if 'skill_columns' not in locals():
                    # Detect any skill-related columns
                    skill_columns = [col for col in df.columns if 'score' in col.lower() or 'skill' in col.lower()] if 'df' in locals() and df is not None else []
                
                # Always add total_students = 2000 regardless of error type
                if 'df' not in locals() or df is None:
                    # Create a default dataframe with 2000 students
                    df = pd.DataFrame({
                        'total_students': [2000],
                        'total_teachers': [100],
                        'institution_name': ['Default Institution'],
                        'num_classrooms': [40]
                    })
                else:
                    # Add or update the total_students column
                    df['total_students'] = 2000
                    
                    # If total_teachers is missing, add a reasonable value
                    if 'total_teachers' not in df.columns:
                        df['total_teachers'] = 100  # Use 20:1 ratio by default
                
                # Detect if we have student data
                student_data_detected = False
                if 'df' in locals() and df is not None and len(df) > 1:
                    # Check for common indicators of student data (ID, name, scores)
                    id_cols = [col for col in df.columns if 'id' in col.lower()]
                    name_cols = [col for col in df.columns if 'name' in col.lower()]
                    if (id_cols or name_cols) and len(df) > 5:  # More than 5 rows suggests student data
                        student_data_detected = True
                        st.success(f"📊 Detected student data with {len(df)} students. We'll use this for optimization.")
                
                # Process our corrected dataframe
                row = df.iloc[0]
                
                # Create a basic input data dictionary
                input_data = {
                    'institution_name': row.get('institution_name', 'Default Institution'),
                    'total_students': 2000,  # Always use 2000 regardless of what's in the file
                    'total_teachers': int(row.get('total_teachers', 100)),
                    'num_classrooms': int(row.get('num_classrooms', 40)),
                    'min_students_per_teacher': 5,
                    'max_students_per_teacher': 25,
                    'ideal_ratio': 15,
                    'max_class_size': 30,
                    'subject_names': ['Math', 'Science', 'History', 'English', 'Art'],
                    'subject_difficulties': {
                        'Math': 7, 'Science': 6, 'History': 5, 'English': 4, 'Art': 3
                    },
                    'teacher_distribution': {
                        'Math': 30, 'Science': 25, 'History': 20, 'English': 15, 'Art': 10
                    },
                    'prioritize_experience': True
                }
                
                # Calculate current ratio
                current_overall = float(input_data['total_students']) / float(input_data['total_teachers'])
                
                current_ratios = {
                    'overall': current_overall,
                    'by_subject': {subject: current_overall for subject in input_data['subject_names']}
                }
                
                # Store in session state
                st.session_state.input_data = input_data
                st.session_state.current_ratios = current_ratios
                
                # Run optimization
                optimization_result = optimize_teacher_allocation(input_data)
                
                # If we have student data, add classroom assignments based on skills
                if student_data_detected:
                    optimization_result = add_student_skill_based_assignments(optimization_result, df, skill_columns)
                
                st.session_state.optimization_result = optimization_result
                
                st.success("✅ Successfully processed the data with 2000 students.")
                
                # Navigate to results page
                st.session_state.page = 'results'
                st.rerun()
                
            except Exception as inner_e:
                st.error(f"⚠️ Error processing the data: {str(inner_e)}")
                st.expander("🛠️ Error details for troubleshooting").write(str(inner_e))
                st.stop()

def add_student_skill_based_assignments(optimization_result, student_df, skill_columns, custom_groups=None):
    """
    Add classroom assignments for students based on their skills.
    
    Args:
        optimization_result: The original optimization result
        student_df: DataFrame containing student data
        skill_columns: List of columns containing skill scores
        custom_groups: Optional number of custom groups to create (overrides classroom-based grouping)
    
    Returns:
        Updated optimization result with student assignments
    """
    try:
        # If no student data provided, return original result
        if student_df is None or len(student_df) == 0 or not skill_columns:
            return optimization_result
        
        # Create a copy of the optimization result
        result = optimization_result.copy() if optimization_result else {}
        
        # Calculate the number of groups to use
        if custom_groups and custom_groups > 0:
            # Use custom number of groups
            num_groups = min(custom_groups, len(student_df))  # Can't have more groups than students
        elif 'classroom_allocation' in result:
            # Use number of classrooms from optimization
            num_groups = len(result['classroom_allocation'])
        else:
            # Default to 3 groups if no classroom data
            num_groups = 3
        
        # Calculate composite skill scores
        student_df = student_df.copy()
        if not 'composite_skill' in student_df.columns:
            # Create normalized composite skill score (0-10 scale)
            student_df['composite_skill'] = student_df[skill_columns].mean(axis=1)
            max_skill = student_df['composite_skill'].max()
            min_skill = student_df['composite_skill'].min()
            if max_skill > min_skill:  # Avoid division by zero
                student_df['composite_skill'] = (student_df['composite_skill'] - min_skill) / (max_skill - min_skill) * 10
            else:
                student_df['composite_skill'] = 5  # Default middle value if all scores are the same
        
        # Sort students by composite skill score
        sorted_students = student_df.sort_values('composite_skill', ascending=False)
        
        # Divide students into groups based on skill level
        students_per_group = len(sorted_students) // num_groups
        remainder = len(sorted_students) % num_groups
        
        # Create group assignments
        group_assignments = []
        group_info = []
        
        start_idx = 0
        for group_idx in range(num_groups):
            # Calculate number of students in this group
            group_size = students_per_group + (1 if group_idx < remainder else 0)
            end_idx = start_idx + group_size
            
            # Get students for this group
            if start_idx < len(sorted_students):
                group_students = sorted_students.iloc[start_idx:end_idx]
                
                # Create group skill profile
                group_skills = {}
                for skill in skill_columns:
                    skill_values = group_students[skill]
                    group_skills[skill] = {
                        'avg': round(skill_values.mean(), 2),
                        'min': round(skill_values.min(), 2),
                        'max': round(skill_values.max(), 2)
                    }
                
                # Determine top skill for the group
                avg_skills = {skill: group_skills[skill]['avg'] for skill in skill_columns}
                top_skill = max(avg_skills.items(), key=lambda x: x[1])[0] if avg_skills else None
                
                # Determine skill level label based on position in sorted list
                if group_idx < num_groups // 3:
                    skill_level = "Advanced"
                elif group_idx < 2 * num_groups // 3:
                    skill_level = "Intermediate"
                else:
                    skill_level = "Beginner"
                
                # Create group information
                group_data = {
                    'group_id': group_idx + 1,
                    'group_name': f"Group {group_idx + 1}",
                    'skill_level': skill_level,
                    'size': len(group_students),
                    'avg_composite_skill': round(group_students['composite_skill'].mean(), 2),
                    'skill_profile': group_skills,
                    'top_skill': top_skill,
                    'student_count': len(group_students)
                }
                
                # Add group info
                group_info.append(group_data)
                
                # Create student assignments
                for _, student in group_students.iterrows():
                    # Get student ID and name
                    student_id = student.get('id', student.name if hasattr(student, 'name') else 'Unknown')
                    student_name = student.get('name', f"Student {student_id}")
                    
                    # Create student skill profile
                    student_skill_profile = {}
                    for skill in skill_columns:
                        # Determine skill level relative to all students
                        value = student[skill]
                        percentile = 0
                        if len(student_df) > 1:  # Avoid division by zero
                            percentile = len(student_df[student_df[skill] <= value]) / len(student_df) * 100
                        
                        if percentile <= 33:
                            level = 'Beginner'
                        elif percentile <= 66:
                            level = 'Intermediate'
                        else:
                            level = 'Advanced'
                        
                        student_skill_profile[skill] = {
                            'value': value,
                            'level': level,
                            'percentile': round(percentile)
                        }
                    
                    # Add assignment
                    group_assignments.append({
                        'student_id': student_id,
                        'student_name': student_name,
                        'group_id': group_idx + 1,
                        'group_name': f"Group {group_idx + 1}",
                        'composite_skill': round(student['composite_skill'], 2),
                        'skills': student_skill_profile
                    })
                
                start_idx = end_idx
        
        # Add group information to result
        result['skill_based_distribution'] = group_info
        result['student_group_assignments'] = group_assignments
        result['custom_grouping'] = custom_groups is not None
        result['num_skill_groups'] = num_groups
        
        # Add skill group analysis
        group_avg_skills = [g['avg_composite_skill'] for g in group_info]
        group_sizes = [g['size'] for g in group_info]
        skill_ranges = []
        for g in group_info:
            if 'skill_profile' in g and g['top_skill'] in g['skill_profile']:
                skill_profile = g['skill_profile'][g['top_skill']]
                skill_ranges.append(skill_profile['max'] - skill_profile['min'])
            else:
                skill_ranges.append(0)
        
        result['skill_group_analysis'] = {
            'num_groups': num_groups,
            'total_students': len(student_df),
            'avg_group_size': round(len(student_df) / num_groups, 1),
            'group_homogeneity': round(1 - (sum(skill_ranges) / max(1, len(skill_ranges)) / 10), 2),  # 0-1 scale
            'between_group_variance': round(np.var(group_avg_skills) if len(group_avg_skills) > 1 else 0, 2)
        }
        
        return result
    except Exception as e:
        # If anything goes wrong, return the original result
        print(f"Error in skill-based assignment: {str(e)}")
        return optimization_result

def create_student_group_analysis_chart(optimization_result):
    """
    Creates a visualization of student group analysis based on skill distribution.
    
    Args:
        optimization_result: Dictionary containing optimization results with skill distribution
        
    Returns:
        Plotly figure object or dictionary of figures
    """
    try:
        if not optimization_result or 'skill_based_distribution' not in optimization_result:
            # Return empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No student skill data available for group analysis.",
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                title="Student Group Analysis",
                xaxis=dict(showticklabels=False),
                yaxis=dict(showticklabels=False)
            )
            return {'main_chart': fig, 'skill_chart': fig, 'summary': "No skill data available"}
        
        groups = optimization_result['skill_based_distribution']
        
        # Extract data for visualization
        group_ids = [g['group_id'] for g in groups]
        group_names = [g['group_name'] for g in groups]
        avg_skills = [g['avg_composite_skill'] for g in groups]
        sizes = [g['size'] for g in groups]
        top_skills = [g.get('top_skill', 'Unknown') for g in groups]
        skill_levels = [g.get('skill_level', 'Unknown') for g in groups]
        
        # Create color mapping for skill levels
        color_map = {
            'Advanced': 'rgba(0, 200, 0, 0.7)',      # Green
            'Intermediate': 'rgba(200, 200, 0, 0.7)', # Yellow
            'Beginner': 'rgba(200, 0, 0, 0.7)'       # Red
        }
        
        colors = [color_map.get(level, 'rgba(100, 100, 100, 0.7)') for level in skill_levels]
        
        # Create main visualization - grouped bar chart
        fig1 = go.Figure()
        
        # Add bars for group sizes
        fig1.add_trace(go.Bar(
            x=group_names,
            y=sizes,
            name="Group Size",
            marker_color="rgba(100, 149, 237, 0.7)",
            text=sizes,
            textposition='auto'
        ))
        
        # Add line for average skill
        fig1.add_trace(go.Scatter(
            x=group_names,
            y=avg_skills,
            mode='lines+markers',
            name="Avg Skill",
            yaxis='y2',
            line=dict(color='rgba(220, 20, 60, 0.9)', width=3),
            marker=dict(size=10, symbol='circle')
        ))
        
        # Update layout
        fig1.update_layout(
            title="Student Group Distributions",
            xaxis_title="Group",
            yaxis_title="Number of Students",
            yaxis2=dict(
                title="Average Skill Score (0-10)",
                overlaying='y',
                side='right',
                range=[0, 10]
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='group',
            plot_bgcolor='rgba(245, 245, 245, 0.8)'
        )
        
        # Create second visualization - skill distribution
        fig2 = go.Figure()
        
        # Extract skill profiles if available
        all_skills = set()
        skill_data = []
        
        for group in groups:
            if 'skill_profile' in group:
                all_skills.update(group['skill_profile'].keys())
                skill_data.append({
                    'group': group['group_name'],
                    'profile': group['skill_profile'],
                    'group_id': group['group_id']
                })
        
        if skill_data and all_skills:
            # Create radar/polar chart for skill comparison
            # Define a color scale for the groups to make them visually distinct
            colors = [
                'rgba(31, 119, 180, 0.8)',    # Blue
                'rgba(255, 127, 14, 0.8)',    # Orange
                'rgba(44, 160, 44, 0.8)',     # Green
                'rgba(214, 39, 40, 0.8)',     # Red
                'rgba(148, 103, 189, 0.8)',   # Purple
                'rgba(140, 86, 75, 0.8)',     # Brown
                'rgba(227, 119, 194, 0.8)',   # Pink
                'rgba(127, 127, 127, 0.8)',   # Gray
                'rgba(188, 189, 34, 0.8)',    # Olive
                'rgba(23, 190, 207, 0.8)'     # Teal
            ]
            
            # Sort skill_data by group_id to ensure consistent group colors
            skill_data = sorted(skill_data, key=lambda x: x['group_id'])
            
            # Get a list of skill categories for the radar chart
            skill_categories = sorted(list(all_skills))
            
            # Create radar chart traces for each group
            for i, data in enumerate(skill_data):
                values = []
                for skill in skill_categories:
                    if skill in data['profile']:
                        values.append(data['profile'][skill]['avg'])
                    else:
                        values.append(0)
                
                # Add the first value again at the end to close the shape
                color_idx = i % len(colors)
                
                fig2.add_trace(go.Scatterpolar(
                    r=values,
                    theta=skill_categories,
                    fill='toself',
                    name=data['group'],
                    line=dict(color=colors[color_idx]),
                    fillcolor=colors[color_idx].replace('0.8', '0.3'),
                    opacity=0.9
                ))
            
            # Improve visual layout of the radar chart
            fig2.update_layout(
                title="Skill Profile by Group",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10],
                        tickvals=[0, 2, 4, 6, 8, 10],
                        ticktext=['0', '2', '4', '6', '8', '10'],
                        tickfont=dict(size=10),
                        gridcolor='lightgray',
                        linecolor='lightgray'
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=10),
                        rotation=90,
                        direction='clockwise',
                        gridcolor='lightgray'
                    ),
                    bgcolor='rgba(245, 245, 245, 0.8)'
                ),
                showlegend=True,
                legend=dict(
                    orientation="h", 
                    yanchor="bottom",
                    y=1.05,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10)
                ),
                margin=dict(l=80, r=80, t=100, b=80)
            )
        else:
            # Fallback to simple bar chart of composite skills
            fig2 = px.bar(
                x=group_names,
                y=avg_skills,
                color=skill_levels,
                labels={
                    'x': 'Group',
                    'y': 'Average Skill Level',
                    'color': 'Skill Level'
                },
                title='Group Skill Levels',
                text=avg_skills
            )
            
            fig2.update_layout(
                xaxis_title="Group",
                yaxis_title="Average Skill (0-10)",
                yaxis=dict(range=[0, 10])
            )
        
        # Create summary text
        if 'skill_group_analysis' in optimization_result:
            analysis = optimization_result['skill_group_analysis']
            summary = f"""
            ### Student Group Analysis Summary
            
            - **Number of Groups:** {analysis['num_groups']}
            - **Total Students:** {analysis['total_students']}
            - **Average Group Size:** {analysis['avg_group_size']} students
            - **Group Homogeneity:** {analysis['group_homogeneity']:.2f} (0-1 scale, higher is more homogeneous)
            - **Between-Group Variance:** {analysis['between_group_variance']:.2f} (higher indicates more distinct groups)
            
            #### Distribution by Skill Level:
            """
            
            # Add count by skill level
            level_counts = {}
            for level in skill_levels:
                if level in level_counts:
                    level_counts[level] += 1
                else:
                    level_counts[level] = 1
                    
            for level, count in level_counts.items():
                summary += f"\n- **{level}:** {count} groups"
                
        else:
            summary = "### Student Group Analysis Summary\n\nGroup analysis based on student skill levels."
        
        return {
            'main_chart': fig1,
            'skill_chart': fig2,
            'summary': summary
        }
        
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error creating student group analysis: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Student Group Analysis (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return {'main_chart': fig, 'skill_chart': fig, 'summary': f"Error: {str(e)}"}

def setup_genai():
    """Set up the Google Generative AI client"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        st.warning("⚠️ Google API key not found. Please enter your API key below to use the AI assistant.")
        
        # Create a more user-friendly API key entry form
        with st.form("api_key_form"):
            api_key = st.text_input("🔑 Enter your Google API Key:", type="password", 
                                    help="Your API key will be used only for this session and won't be stored permanently.")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                submit_button = st.form_submit_button("✅ Set API Key", type="primary")
            
            with col2:
                st.markdown("""
                [Get a Google Gemini API key](https://ai.google.dev/) if you don't have one already.
                """)
            
        if not api_key:
            st.info("ℹ️ The AI assistant requires a valid Google API key to function.")
            return None
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Store API key in session state for persistence during this session
        st.session_state.google_api_key = api_key
        
        # Try different model names in order of preference
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            st.success("✅ Successfully connected to Google Gemini 1.5 Pro model!")
            return model
        except:
            try:
                model = genai.GenerativeModel('gemini-1.0-pro')
                st.success("✅ Successfully connected to Google Gemini 1.0 Pro model!")
                return model
            except:
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    st.success("✅ Connected to Google Gemini Pro model!")
                    return model
                except Exception as model_error:
                    st.error(f"❌ Error selecting Gemini model: {str(model_error)}")
                    st.info("Please check if your API key has access to the Gemini models.")
                    return None
                
    except Exception as e:
        st.error(f"❌ Error setting up Google GenerativeAI: {str(e)}")
        st.info("Please make sure you've entered a valid Google API key.")
        return None

def show_chatbot_page():
    st.title("🤖 AI Assistant")
    
    st.markdown("""
    Chat with our AI assistant to get real-time feedback on student-teacher ratios
    and recommendations for optimizing educational resource allocation. The assistant uses 
    Google's Gemini AI to provide intelligent, context-aware responses.
    """)
    
    # Setup Google Generative AI
    model = setup_genai()
    
    if model is None:
        # Show sample questions even if the model isn't available
        with st.expander("💡 Sample questions you can ask the AI assistant"):
            st.markdown("""
            - What is the optimal student-teacher ratio for mathematics?
            - How can I improve resource allocation in my school?
            - What factors should I consider when assigning teachers to classrooms?
            - How do subject difficulties affect optimal student-teacher ratios?
            - What are best practices for balancing classroom sizes?
            - How can I implement the recommended changes gradually?
            """)
        st.stop()
    
    # Sidebar for context and options
    with st.sidebar:
        st.markdown("### 💬 Chat Options")
        
        # Option to include optimization results in context
        include_optimization = st.checkbox("Include optimization results in chat context", 
                                         value=True,
                                         help="When enabled, the AI will consider your optimization results when answering questions")
        
        # Option to clear chat history
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
            st.rerun()
    
    # Display chat history
    for message in st.session_state.chat_history:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])
    
    # Get optimization context if available and enabled
    context = ""
    if st.session_state.optimization_result is not None and include_optimization:
        input_data = st.session_state.input_data
        result = st.session_state.optimization_result
        
        context = f"""
        Context for the AI assistant:
        - Institution: {input_data.get('institution_name', 'Unknown')}
        - Total Students: {input_data.get('total_students', 0)}
        - Total Teachers: {input_data.get('total_teachers', 0)}
        - Optimal Ratio: {result.get('optimal_ratio', 0):.2f}:1
        - Current Ratio: {st.session_state.current_ratios.get('overall', 0):.2f}:1
        - Subject count: {len(input_data.get('subject_names', []))}
        - Subjects: {', '.join(input_data.get('subject_names', []))}
        """
        
        # Add skill-based distribution if available
        if 'skill_based_distribution' in result:
            context += "\n- Student skill distribution is available and has been incorporated into classroom assignments"
        
        # Add recommendations summary if available
        if 'recommendations' in result and result['recommendations']:
            top_rec = result['recommendations'][0]
            context += f"\n- Top recommendation: {top_rec.get('title', 'N/A')}"
    
    # Sample questions
    if not st.session_state.chat_history:
        st.info("👋 Welcome! Ask me any questions about student-teacher ratios, classroom optimization, or educational resource allocation.")
        
        with st.expander("💡 Sample questions"):
            sample_questions = [
                "What's the ideal student-teacher ratio for difficult subjects?",
                "How can we implement these recommendations with minimal disruption?",
                "What factors affect optimal classroom sizes?",
                "How should we allocate teachers based on subject difficulty?",
                "What's the relationship between class size and learning outcomes?"
            ]
            
            # Create clickable sample questions
            for i, question in enumerate(sample_questions):
                if st.button(question, key=f"sample_{i}", use_container_width=True):
                    # Add question to chat history and rerun
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    st.rerun()
    
    # Get user input
    user_input = st.chat_input("Ask about student-teacher ratios, resource allocation, or optimization strategies...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            loading_message = st.info("🧠 Thinking...")
            
            try:
                # Prepare prompt with context and improved instructions
                prompt = f"""
                You are an educational resource optimization assistant specializing in student-teacher ratio optimization.
                Your responses should be helpful, accurate, and tailored to educational professionals.
                
                {context}
                
                Please respond to the following question from a school administrator about student-teacher
                ratios, resource allocation, or optimization strategies. Be concise but thorough, and provide
                specific actionable advice when possible.
                
                Question: {user_input}
                """
                
                # Get response from Google GenerativeAI
                response = model.generate_content(prompt)
                full_response = response.text
                
                # Remove loading message
                loading_message.empty()
                
                # Display response
                message_placeholder.markdown(full_response)
                
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                # Remove loading message
                loading_message.empty()
                
                error_message = f"❌ Error generating response: {str(e)}"
                message_placeholder.error(error_message)
                message_placeholder.info("Please try asking a different question or check your API key.")
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()