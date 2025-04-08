import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from visualization import (
    create_current_vs_optimal_chart,
    create_allocation_chart,
    create_heatmap,
    create_classroom_balance_chart,
    create_recommendation_impact_chart
)

def generate_report(input_data, current_ratios, optimization_result, report_type, include_visualizations, include_raw_data):
    """
    Generates a report based on input data and optimization results.
    
    Args:
        input_data: Dictionary containing input parameters
        current_ratios: Dictionary containing current ratios
        optimization_result: Dictionary containing optimization results
        report_type: Type of report to generate
        include_visualizations: Whether to include visualizations
        include_raw_data: Whether to include raw data tables
        
    Returns:
        Dictionary containing report sections
    """
    try:
        if report_type == "Executive Summary":
            return generate_executive_summary(input_data, current_ratios, optimization_result, 
                                             include_visualizations, include_raw_data)
        elif report_type == "Detailed Allocation Report":
            return generate_detailed_allocation_report(input_data, current_ratios, optimization_result, 
                                                      include_visualizations, include_raw_data)
        elif report_type == "Recommendation Implementation Plan":
            return generate_recommendation_plan(input_data, current_ratios, optimization_result, 
                                              include_visualizations, include_raw_data)
        elif report_type == "Resource Needs Assessment":
            return generate_resource_assessment(input_data, current_ratios, optimization_result, 
                                               include_visualizations, include_raw_data)
        else:
            # Default to executive summary
            return generate_executive_summary(input_data, current_ratios, optimization_result, 
                                             include_visualizations, include_raw_data)
    except Exception as e:
        # Return an error report
        return {
            'title': 'Error Generating Report',
            'summary': f"An error occurred while generating the report: {str(e)}",
            'sections': [{
                'title': 'Troubleshooting Suggestions',
                'content': """
                - Please try running the optimization again with different parameters
                - Check that all required data is present in your input
                - Verify that your CSV upload contains all necessary columns
                - Try a different report type
                """
            }],
            'conclusion': "If the problem persists, please contact support for assistance."
        }

def generate_executive_summary(input_data, current_ratios, optimization_result, include_visualizations, include_raw_data):
    """
    Generates an executive summary report.
    
    Returns:
        Dictionary containing report sections
    """
    try:
        institution_name = input_data.get('institution_name', 'Your Institution')
        
        # Calculate improvement percentages
        current_overall = current_ratios['overall']
        optimal_overall = optimization_result['optimal_ratio']
        ratio_change = ((optimal_overall - current_overall) / current_overall) * 100
        
        # Get top recommendations
        recommendations = optimization_result.get('recommendations', [])
        top_recommendations = []
        
        if recommendations:
            # Sort by impact score safely
            top_recommendations = sorted(
                recommendations, 
                key=lambda x: x.get('impact_score', 0), 
                reverse=True
            )[:min(3, len(recommendations))]  # Top 3 recommendations or fewer if not enough
        
        # Prepare report
        report = {
            'title': f'Executive Summary: Student-Teacher Ratio Optimization for {institution_name}',
            'summary': f"""
            This executive summary presents the key findings and recommendations from our 
            Student-Teacher Ratio Optimization analysis for {institution_name}. Our analysis 
            used advanced machine learning and constraint optimization techniques to determine 
            the optimal allocation of {input_data['total_teachers']} teachers across 
            {input_data['num_classrooms']} classrooms, taking into account subject difficulty, 
            teacher experience, and other critical educational factors.
            """,
            'sections': [],
            'conclusion': f"""
            By implementing the recommended student-teacher ratios and allocation strategies, 
            {institution_name} can expect to see improved educational outcomes, more balanced 
            workloads for teachers, and more efficient resource utilization. We recommend 
            phased implementation of these changes with regular assessment of their impact on 
            both educational metrics and teacher satisfaction.
            """
        }
        
        # Key Findings Section
        key_findings = {
            'title': 'Key Findings',
            'content': f"""
            - **Current Overall Ratio**: {current_overall:.2f}:1
            - **Optimal Overall Ratio**: {optimal_overall:.2f}:1
            - **Change**: {abs(ratio_change):.1f}% {'increase' if ratio_change > 0 else 'decrease'}
            
            Our analysis shows that the optimal student-teacher ratio for your institution is 
            **{optimal_overall:.2f}:1**, which balances educational outcomes with resource constraints.
            """
        }
        
        # Safely get top difficult subjects
        if 'subject_difficulties' in input_data and input_data['subject_difficulties']:
            try:
                top_difficult_subjects = [s for s, d in sorted(
                    input_data['subject_difficulties'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:min(2, len(input_data['subject_difficulties']))]]
                
                key_findings['content'] += f"""
                
                Subject-specific findings reveal that more difficult subjects like 
                {', '.join(top_difficult_subjects)} 
                benefit from lower ratios, while less challenging subjects can maintain effectiveness with higher ratios.
                """
            except Exception:
                # Skip this part if there's an error
                pass
        
        if include_visualizations:
            try:
                key_findings['visualization'] = create_current_vs_optimal_chart(
                    current_ratios, 
                    optimization_result
                )
            except Exception as e:
                # Skip visualization if there's an error
                key_findings['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
        
        report['sections'].append(key_findings)
        
        # Allocation Strategy Section
        allocation_strategy = {
            'title': 'Optimal Allocation Strategy',
            'content': f"""
            Our optimization model recommends the following allocation strategy:
            
            - Allocate teacher resources according to subject difficulty, with more teachers assigned to challenging subjects
            - Maintain balanced classroom sizes, with an average of {input_data['total_students'] / input_data['num_classrooms']:.1f} students per classroom
            - Ensure that student-teacher ratios stay within the recommended range of {input_data.get('min_students_per_teacher', 5)} to {input_data.get('max_students_per_teacher', 25)}
            """
        }
        
        if include_visualizations:
            try:
                allocation_strategy['visualization'] = create_allocation_chart(optimization_result)
            except Exception as e:
                # Skip visualization if there's an error
                allocation_strategy['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
        
        if include_raw_data and 'subject_allocation' in optimization_result:
            try:
                # Create a table for subject allocation
                subject_data = []
                for subject, details in optimization_result['subject_allocation'].items():
                    subject_data.append({
                        "Subject": subject,
                        "Teachers Allocated": details['teachers_allocated'],
                        "Students Allocated": details['students_allocated'],
                        "Ratio": f"{details['ratio']:.2f}:1",
                        "Difficulty": input_data['subject_difficulties'].get(subject, 'N/A') if 'subject_difficulties' in input_data else 'N/A'
                    })
                
                allocation_strategy['table'] = pd.DataFrame(subject_data)
            except Exception:
                # Skip table if there's an error
                pass
        
        report['sections'].append(allocation_strategy)
        
        # Top Recommendations Section if we have recommendations
        if top_recommendations:
            top_recs_section = {
                'title': 'Top Recommendations',
                'content': f"""
                Based on our analysis, we recommend the following key actions to optimize 
                student-teacher ratios at {institution_name}:
                """
            }
            
            # Add recommendations safely
            for i, rec in enumerate(top_recommendations, 1):
                if i <= 3 and 'title' in rec and 'description' in rec:
                    top_recs_section['content'] += f"""
                    
                    {i}. **{rec['title']}**: {rec['description']}
                    """
            
            if include_visualizations and len(recommendations) >= 3:
                try:
                    top_recs_section['visualization'] = create_recommendation_impact_chart(recommendations)
                except Exception as e:
                    # Skip visualization if there's an error
                    top_recs_section['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
            
            report['sections'].append(top_recs_section)
        
        # Implementation Timeline Section
        implementation = {
            'title': 'Implementation Timeline',
            'content': f"""
            We recommend a phased implementation approach:
            
            - **Phase 1 (1-3 months)**: Implement overall ratio adjustments and quick-win recommendations
            - **Phase 2 (3-6 months)**: Adjust subject-specific allocations and classroom balancing
            - **Phase 3 (6-12 months)**: Develop long-term staffing strategy and continuous improvement process
            """
        }
        
        if include_visualizations:
            try:
                # Create more robust Gantt chart for timeline
                # First check if we have timeline data in the recommendations
                timeline_data = []
                
                # If we have top recommendations with timeline data, use those
                if top_recommendations and any('timeline' in rec for rec in top_recommendations):
                    for rec in top_recommendations:
                        if 'timeline' in rec:
                            timeline_data.append({
                                'Recommendation': rec['title'],
                                'Start': rec['timeline'].get('start', 0),
                                'Duration': rec['timeline'].get('duration', 4)
                            })
                
                # If we don't have timeline data, create default implementation phases
                if not timeline_data:
                    # Create default timeline with key phases
                    timeline_data = [
                        {
                            'Recommendation': 'Adjust Overall Student-Teacher Ratio',
                            'Start': 0,
                            'Duration': 4
                        },
                        {
                            'Recommendation': 'Balance Classroom Allocations',
                            'Start': 2,
                            'Duration': 6
                        },
                        {
                            'Recommendation': 'Optimize Subject-Specific Ratios',
                            'Start': 4,
                            'Duration': 8
                        },
                        {
                            'Recommendation': 'Implement Teacher Utilization Improvements',
                            'Start': 6,
                            'Duration': 10
                        },
                        {
                            'Recommendation': 'Develop Long-Term Staffing Strategy',
                            'Start': 8,
                            'Duration': 12
                        }
                    ]
                
                # Create the visualization from our data
                df = pd.DataFrame(timeline_data)
                
                # Calculate end dates for the Gantt chart
                df['End'] = df['Start'] + df['Duration']
                
                # Create a more attractive color scale
                colorscale = [
                    [0, '#4575b4'],       # Blue for short durations
                    [0.33, '#91bfdb'],    # Light blue
                    [0.66, '#fc8d59'],    # Orange
                    [1, '#d73027']        # Red for long durations
                ]
                
                # Create the timeline figure
                fig = px.timeline(
                    df, 
                    x_start='Start', 
                    x_end='End',
                    y='Recommendation',
                    color='Duration',
                    color_continuous_scale=colorscale,
                    title='Implementation Timeline (Weeks)',
                    labels={"Duration": "Duration (weeks)"}
                )
                
                # Update layout for better appearance
                fig.update_yaxes(autorange="reversed")
                
                # Add vertical grid lines to mark months
                fig.update_layout(
                    xaxis=dict(
                        title='Timeline (weeks)',
                        gridcolor='lightgray',
                        dtick=4,  # Grid lines every 4 weeks (roughly a month)
                        zeroline=True,
                        zerolinecolor='darkgray'
                    ),
                    height=max(300, 100 + len(df) * 40),  # Dynamic height based on number of items
                    plot_bgcolor='rgba(245, 245, 245, 0.8)',
                    margin=dict(l=20, r=20, t=60, b=40)
                )
                
                # Add the figure to the implementation section
                implementation['visualization'] = fig
                
            except Exception as e:
                # Create a fallback visualization if there's an error
                fig = go.Figure()
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"Implementation timeline will be customized based on your school's specific needs",
                    showarrow=False,
                    font=dict(size=14)
                )
                fig.update_layout(
                    title='Implementation Timeline',
                    xaxis=dict(
                        title='Timeline (weeks)',
                        gridcolor='lightgray',
                        showticklabels=True,
                        range=[0, 24]
                    ),
                    yaxis=dict(
                        showticklabels=False
                    ),
                    height=250,
                    plot_bgcolor='rgba(245, 245, 245, 0.8)'
                )
                implementation['visualization'] = fig
        
        report['sections'].append(implementation)
        
        return report
    except Exception as e:
        # Return a simple error report
        return {
            'title': 'Executive Summary (Error)',
            'summary': f"An error occurred while generating the executive summary: {str(e)}",
            'sections': [{
                'title': 'Error Details',
                'content': f"Technical details: {str(e)}"
            }],
            'conclusion': "Please try running the optimization again with different parameters."
        }

def generate_detailed_allocation_report(input_data, current_ratios, optimization_result, include_visualizations, include_raw_data):
    """
    Generates a detailed allocation report.
    
    Returns:
        Dictionary containing report sections
    """
    try:
        institution_name = input_data.get('institution_name', 'Your Institution')
        
        # Prepare report
        report = {
            'title': f'Detailed Allocation Report for {institution_name}',
            'summary': f"""
            This report provides a comprehensive analysis of the optimal allocation of 
            {input_data['total_teachers']} teachers and {input_data['total_students']} students 
            across {input_data['num_classrooms']} classrooms at {institution_name}. It details 
            subject-specific allocations, classroom assignments, and individual teacher workloads, 
            all optimized to balance educational outcomes with resource efficiency.
            """,
            'sections': [],
            'conclusion': f"""
            The detailed allocation plan presented in this report is designed to maximize 
            educational effectiveness while ensuring balanced workloads. Implementation 
            should be monitored closely, with adjustments made as needed based on feedback 
            from teachers, students, and administrative staff. Regular assessment of key 
            performance indicators will help track the impact of these changes on educational outcomes.
            """
        }
        
        # Subject Allocation Section
        subject_allocation = {
            'title': 'Subject-Specific Allocation',
            'content': f"""
            Our optimization model has determined the ideal allocation of teachers and students 
            across different subjects, taking into account subject difficulty, teacher expertise, 
            and educational requirements.
            
            Key insights:
            """
        }
        
        # Safely add subject difficulty insights
        if 'subject_difficulties' in input_data and input_data['subject_difficulties']:
            try:
                top_difficult_subjects = [s for s, d in sorted(
                    input_data['subject_difficulties'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:min(2, len(input_data['subject_difficulties']))]]
                
                subject_allocation['content'] += f"""
                - More challenging subjects like {', '.join(top_difficult_subjects)} have been allocated more teaching resources per student
                """
            except Exception:
                # Skip this part if there's an error
                pass
        
        # Add general insights
        subject_allocation['content'] += f"""
            - The average ratio across all subjects is {optimization_result['optimal_ratio']:.2f}:1
            - Subject difficulty has been weighted as a key factor in determining appropriate ratios
        """
        
        if include_visualizations:
            try:
                subject_allocation['visualization'] = create_allocation_chart(optimization_result)
            except Exception as e:
                # Skip visualization if there's an error
                subject_allocation['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
        
        if include_raw_data and 'subject_allocation' in optimization_result:
            try:
                # Create a detailed table for subject allocation
                subject_data = []
                for subject, details in optimization_result['subject_allocation'].items():
                    # Safely calculate change percentage
                    current_ratio = current_ratios['by_subject'].get(subject, details['ratio'])
                    change_pct = ((details['ratio'] - current_ratio) / current_ratio * 100) if current_ratio else 0
                    
                    subject_data.append({
                        "Subject": subject,
                        "Teachers Allocated": details['teachers_allocated'],
                        "Students Allocated": details['students_allocated'],
                        "Optimal Ratio": f"{details['ratio']:.2f}:1",
                        "Current Ratio": f"{current_ratio:.2f}:1",
                        "Change (%)": f"{change_pct:.1f}%",
                        "Subject Difficulty": input_data['subject_difficulties'].get(subject, 'N/A') if 'subject_difficulties' in input_data else 'N/A'
                    })
                
                subject_allocation['table'] = pd.DataFrame(subject_data)
            except Exception:
                # Skip table if there's an error
                pass
        
        report['sections'].append(subject_allocation)
        
        # Classroom Allocation Section
        classroom_allocation = {
            'title': 'Classroom Assignment Analysis',
            'content': f"""
            The optimized allocation plan distributes students and teachers across 
            {input_data['num_classrooms']} classrooms, ensuring balanced class sizes and 
            appropriate student-teacher ratios.
            
            Key points:
            - Maximum classroom size is limited to {input_data.get('max_class_size', 30)} students
            - Each classroom has been assigned an appropriate mix of subjects
            - Teacher distribution has been optimized to minimize variation in ratios between classrooms
            """
        }
        
        if include_visualizations:
            try:
                classroom_allocation['visualization'] = create_heatmap(optimization_result)
            except Exception as e:
                # Skip visualization if there's an error
                classroom_allocation['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
        
        if include_raw_data and 'classroom_allocation' in optimization_result:
            try:
                # Create a detailed table for classroom allocation
                classroom_data = []
                for i, classroom in enumerate(optimization_result['classroom_allocation']):
                    classroom_data.append({
                        "Classroom": f"Classroom {i+1}",
                        "Teachers Assigned": classroom['teachers_assigned'],
                        "Students Assigned": classroom['students_assigned'],
                        "Ratio": f"{classroom['ratio']:.2f}:1",
                        "Subjects": ", ".join(classroom.get('subjects', [])),
                        "Utilization (%)": f"{(classroom['students_assigned'] / input_data.get('max_class_size', 30) * 100):.1f}%"
                    })
                
                classroom_allocation['table'] = pd.DataFrame(classroom_data)
            except Exception:
                # Skip table if there's an error
                pass
        
        report['sections'].append(classroom_allocation)
        
        # Teacher Allocation Section
        teacher_allocation = {
            'title': 'Individual Teacher Workload Analysis',
            'content': f"""
            Our optimization model has determined the optimal student assignment for each teacher, 
            ensuring balanced workloads while respecting constraints such as subject expertise and 
            minimum/maximum students per teacher.
            """
        }
        
        # Add more details if available
        if 'teacher_allocation' in optimization_result and optimization_result['teacher_allocation']:
            try:
                avg_utilization = sum(t.get('utilization', 0) for t in optimization_result['teacher_allocation']) / len(optimization_result['teacher_allocation'])
                
                teacher_allocation['content'] += f"""
                
                Key findings:
                - Average teacher utilization is {avg_utilization:.1f}%
                - Each teacher has been assigned between {input_data.get('min_students_per_teacher', 5)} and {input_data.get('max_students_per_teacher', 25)} students
                """
            except Exception:
                # Skip this part if there's an error
                pass
            
            # Add teacher distribution if available
            if 'teacher_distribution' in input_data and input_data['teacher_distribution']:
                try:
                    teacher_distribution_text = ', '.join([f"{s}: {p:.1f}%" for s, p in input_data['teacher_distribution'].items()])
                    teacher_allocation['content'] += f"- Teachers are allocated to subjects according to the distribution specified: {teacher_distribution_text}\n"
                except Exception:
                    # Skip this part if there's an error
                    pass
        
        if include_visualizations and 'teacher_allocation' in optimization_result and optimization_result['teacher_allocation']:
            try:
                # Create teacher utilization chart
                teacher_ids = [f"T{i+1}" for i in range(len(optimization_result['teacher_allocation']))]
                utilization = [t.get('utilization', 0) for t in optimization_result['teacher_allocation']]
                students = [t.get('students_assigned', 0) for t in optimization_result['teacher_allocation']]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=teacher_ids,
                    y=utilization,
                    name='Utilization (%)',
                    marker_color='indianred'
                ))
                
                fig.add_trace(go.Bar(
                    x=teacher_ids,
                    y=students,
                    name='Students Assigned',
                    marker_color='royalblue',
                    yaxis='y2'
                ))
                
                # Update layout with two y-axes
                fig.update_layout(
                    title='Teacher Workload and Utilization',
                    xaxis=dict(title='Teacher ID'),
                    yaxis=dict(
                        title='Utilization (%)',
                        side='left'
                    ),
                    yaxis2=dict(
                        title='Students Assigned',
                        side='right',
                        overlaying='y'
                    ),
                    barmode='group',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                teacher_allocation['visualization'] = fig
            except Exception as e:
                # Skip visualization if there's an error
                teacher_allocation['content'] += f"\n\n*Note: Visualization could not be generated: {str(e)}*"
        
        if include_raw_data and 'teacher_allocation' in optimization_result and optimization_result['teacher_allocation']:
            try:
                # Create a detailed table for teacher allocation
                teacher_data = []
                for i, teacher in enumerate(optimization_result['teacher_allocation']):
                    teacher_data.append({
                        "Teacher ID": f"T{i+1}",
                        "Subject": teacher.get('subject', 'Unknown'),
                        "Students Assigned": teacher.get('students_assigned', 0),
                        "Classroom": teacher.get('classroom', 'Unknown'),
                        "Utilization (%)": f"{teacher.get('utilization', 0):.1f}%"
                    })
                
                teacher_allocation['table'] = pd.DataFrame(teacher_data)
            except Exception:
                # Skip table if there's an error
                pass
        
        report['sections'].append(teacher_allocation)
        
        # Add Skill-Based Distribution section if available
        if 'skill_based_distribution' in optimization_result:
            skill_section = {
                'title': 'Student Skill-Based Distribution',
                'content': """
                Based on the student skill data provided, we've analyzed how students with different
                skill levels should be distributed across classrooms for optimal learning outcomes.
                
                Key insights:
                - Students are grouped to ensure a balance of skill levels in each classroom
                - This approach helps prevent learning disparities and encourages peer learning
                - The distribution maximizes the effectiveness of the allocated teacher resources
                """
            }
            
            if include_raw_data:
                try:
                    # Create a table showing the distribution of skill levels
                    skill_data = []
                    for skill, levels in optimization_result['skill_based_distribution'].items():
                        skill_data.append({
                            "Skill": skill.replace('_', ' ').title(),
                            "Low Level Students": levels.get('low', 0),
                            "Medium Level Students": levels.get('medium', 0),
                            "High Level Students": levels.get('high', 0),
                            "Total Students": sum(levels.values())
                        })
                    
                    skill_section['table'] = pd.DataFrame(skill_data)
                except Exception:
                    # Skip table if there's an error
                    pass
            
            if include_visualizations:
                try:
                    # Create a visualization of skill distribution
                    skill_viz_data = []
                    for skill, levels in optimization_result['skill_based_distribution'].items():
                        for level, count in levels.items():
                            skill_viz_data.append({
                                'Skill': skill.replace('_', ' ').title(),
                                'Level': level.title(),
                                'Count': count
                            })
                    
                    df = pd.DataFrame(skill_viz_data)
                    fig = px.bar(
                        df,
                        x='Skill',
                        y='Count',
                        color='Level',
                        title='Student Distribution by Skill Level',
                        barmode='group'
                    )
                    
                    skill_section['visualization'] = fig
                except Exception:
                    # Skip visualization if there's an error
                    pass
            
            report['sections'].append(skill_section)
        
        return report
    except Exception as e:
        # Return a simple error report
        return {
            'title': 'Detailed Allocation Report (Error)',
            'summary': f"An error occurred while generating the detailed allocation report: {str(e)}",
            'sections': [{
                'title': 'Error Details',
                'content': f"Technical details: {str(e)}"
            }],
            'conclusion': "Please try running the optimization again with different parameters."
        }

def generate_recommendation_plan(input_data, current_ratios, optimization_result, include_visualizations, include_raw_data):
    """
    Generates a recommendation implementation plan report.
    
    Returns:
        Dictionary containing report sections
    """
    try:
        institution_name = input_data.get('institution_name', 'Your Institution')
        
        # Get recommendations
        recommendations = optimization_result.get('recommendations', [])
        
        # Prepare report
        report = {
            'title': f'Implementation Plan for {institution_name}',
            'summary': f"""
            This implementation plan outlines the strategic approach for optimizing 
            student-teacher ratios at {institution_name}. It provides a detailed roadmap 
            for executing the recommendations from our analysis, including timelines, 
            responsible stakeholders, and expected outcomes.
            """,
            'sections': [],
            'conclusion': f"""
            Successful implementation of this plan will lead to improved educational outcomes 
            and resource efficiency at {institution_name}. Regular monitoring of progress against 
            key performance indicators is essential, with adjustments made as needed based on 
            ongoing feedback and changing circumstances.
            """
        }
        
        # Overview Section
        overview = {
            'title': 'Implementation Overview',
            'content': f"""
            This plan covers the implementation of {len(recommendations)} recommendations 
            designed to optimize the student-teacher ratio at {institution_name}. The approach 
            is divided into three phases:
            
            1. **Short-term (1-3 months)**: Quick wins and immediate adjustments
            2. **Medium-term (3-6 months)**: Structural changes and process improvements
            3. **Long-term (6-12 months)**: Systemic reforms and continuous improvement
            
            Implementation should be guided by the following principles:
            
            - Regular assessment of progress and outcomes
            - Stakeholder engagement and transparent communication
            - Flexibility to adapt as needed based on feedback
            - Balance between educational quality and resource efficiency
            """
        }
        
        report['sections'].append(overview)
        
        # Add recommendation sections if available
        if recommendations:
            # Sort recommendations by timeline (start date)
            sorted_recommendations = sorted(
                recommendations,
                key=lambda x: x.get('timeline', {}).get('start', 100) if 'timeline' in x else 100
            )
            
            # Group recommendations by phase
            short_term = []
            medium_term = []
            long_term = []
            
            for rec in sorted_recommendations:
                start = rec.get('timeline', {}).get('start', 0) if 'timeline' in rec else 0
                if start < 4:
                    short_term.append(rec)
                elif start < 12:
                    medium_term.append(rec)
                else:
                    long_term.append(rec)
            
            # Short-term recommendations
            if short_term:
                short_term_section = {
                    'title': 'Short-term Implementation (1-3 months)',
                    'content': """
                    These recommendations should be implemented within the first three months. 
                    They are primarily focused on quick wins and immediate adjustments that can 
                    be made with minimal disruption to existing operations.
                    
                    **Key recommendations:**
                    """
                }
                
                for i, rec in enumerate(short_term, 1):
                    short_term_section['content'] += f"""
                    
                    {i}. **{rec.get('title', 'Recommendation')}**
                       - Description: {rec.get('description', 'No description provided')}
                       - Timeline: Start in week {rec.get('timeline', {}).get('start', 0) if 'timeline' in rec else 'N/A'}, duration of {rec.get('timeline', {}).get('duration', 0) if 'timeline' in rec else 'N/A'} weeks
                       - Impact: {rec.get('impact', 'N/A')}
                    """
                    
                    # Add action items if available
                    if 'action_items' in rec and rec['action_items']:
                        short_term_section['content'] += """
                       - Action items:
                        """
                        for item in rec['action_items']:
                            short_term_section['content'] += f"""
                            - {item}
                            """
                
                report['sections'].append(short_term_section)
            
            # Medium-term recommendations
            if medium_term:
                medium_term_section = {
                    'title': 'Medium-term Implementation (3-6 months)',
                    'content': """
                    These recommendations require more planning and coordination to implement 
                    and should be addressed in the medium term. They focus on structural changes 
                    and process improvements.
                    
                    **Key recommendations:**
                    """
                }
                
                for i, rec in enumerate(medium_term, 1):
                    medium_term_section['content'] += f"""
                    
                    {i}. **{rec.get('title', 'Recommendation')}**
                       - Description: {rec.get('description', 'No description provided')}
                       - Timeline: Start in week {rec.get('timeline', {}).get('start', 0) if 'timeline' in rec else 'N/A'}, duration of {rec.get('timeline', {}).get('duration', 0) if 'timeline' in rec else 'N/A'} weeks
                       - Impact: {rec.get('impact', 'N/A')}
                    """
                    
                    # Add action items if available
                    if 'action_items' in rec and rec['action_items']:
                        medium_term_section['content'] += """
                       - Action items:
                        """
                        for item in rec['action_items']:
                            medium_term_section['content'] += f"""
                            - {item}
                            """
                
                report['sections'].append(medium_term_section)
            
            # Long-term recommendations
            if long_term:
                long_term_section = {
                    'title': 'Long-term Implementation (6-12 months)',
                    'content': """
                    These recommendations focus on systemic reforms and continuous improvement. 
                    They require substantial planning, resource allocation, and stakeholder buy-in.
                    
                    **Key recommendations:**
                    """
                }
                
                for i, rec in enumerate(long_term, 1):
                    long_term_section['content'] += f"""
                    
                    {i}. **{rec.get('title', 'Recommendation')}**
                       - Description: {rec.get('description', 'No description provided')}
                       - Timeline: Start in week {rec.get('timeline', {}).get('start', 0) if 'timeline' in rec else 'N/A'}, duration of {rec.get('timeline', {}).get('duration', 0) if 'timeline' in rec else 'N/A'} weeks
                       - Impact: {rec.get('impact', 'N/A')}
                    """
                    
                    # Add action items if available
                    if 'action_items' in rec and rec['action_items']:
                        long_term_section['content'] += """
                       - Action items:
                        """
                        for item in rec['action_items']:
                            long_term_section['content'] += f"""
                            - {item}
                            """
                
                report['sections'].append(long_term_section)
            
            # Add timeline visualization
            if include_visualizations and recommendations:
                try:
                    # Create Gantt chart
                    timeline_data = []
                    for rec in sorted_recommendations:
                        if 'timeline' in rec:
                            timeline_data.append({
                                'Recommendation': rec.get('title', 'Unnamed'),
                                'Start': rec['timeline'].get('start', 0),
                                'Duration': rec['timeline'].get('duration', 4),
                                'Impact': rec.get('impact_score', 5)
                            })
                    
                    if timeline_data:
                        timeline_df = pd.DataFrame(timeline_data)
                        
                        # Add end column
                        timeline_df['End'] = timeline_df['Start'] + timeline_df['Duration']
                        
                        # Create figure
                        fig = px.timeline(
                            timeline_df, 
                            x_start='Start', 
                            x_end='End',
                            y='Recommendation',
                            color='Impact',
                            title='Implementation Timeline (Weeks)',
                            color_continuous_scale='Viridis'
                        )
                        
                        fig.update_yaxes(autorange="reversed")
                        fig.update_layout(
                            xaxis=dict(title='Week Number'),
                            yaxis=dict(title=''),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        # Add phase markers
                        fig.add_shape(
                            type="line",
                            x0=4, y0=-0.5,
                            x1=4, y1=len(timeline_df) - 0.5,
                            line=dict(color="red", width=1, dash="dash")
                        )
                        
                        fig.add_shape(
                            type="line",
                            x0=12, y0=-0.5,
                            x1=12, y1=len(timeline_df) - 0.5,
                            line=dict(color="red", width=1, dash="dash")
                        )
                        
                        # Add phase labels
                        fig.add_annotation(
                            x=2, y=len(timeline_df),
                            text="Short-term",
                            showarrow=False,
                            yshift=20
                        )
                        
                        fig.add_annotation(
                            x=8, y=len(timeline_df),
                            text="Medium-term",
                            showarrow=False,
                            yshift=20
                        )
                        
                        fig.add_annotation(
                            x=18, y=len(timeline_df),
                            text="Long-term",
                            showarrow=False,
                            yshift=20
                        )
                        
                        # Add to report
                        timeline_section = {
                            'title': 'Implementation Timeline',
                            'content': """
                            The following Gantt chart illustrates the timeline for implementing 
                            all recommendations. The horizontal axis represents weeks from the 
                            start of implementation, while color represents the impact level of each recommendation.
                            
                            Note the phases of implementation:
                            - Short-term: Weeks 1-4
                            - Medium-term: Weeks 5-12
                            - Long-term: Weeks 13+
                            """,
                            'visualization': fig
                        }
                        
                        report['sections'].append(timeline_section)
                except Exception:
                    # Skip if there's an error
                    pass
        
        # Add KPI monitoring section
        monitoring_section = {
            'title': 'Monitoring and Evaluation',
            'content': f"""
            To ensure successful implementation, {institution_name} should establish a 
            monitoring and evaluation framework with the following key performance indicators (KPIs):
            
            **Educational Outcomes:**
            - Student academic performance by subject
            - Student satisfaction and engagement
            - Parent feedback on educational quality
            
            **Resource Efficiency:**
            - Actual vs. target student-teacher ratios
            - Teacher workload and utilization
            - Classroom space utilization
            
            **Implementation Progress:**
            - Percentage of recommendations implemented on schedule
            - Stakeholder feedback on implementation process
            - Identified obstacles and mitigation strategies
            
            Regular review meetings should be scheduled to assess progress against these KPIs, 
            with adjustments made to the implementation plan as needed.
            """
        }
        
        report['sections'].append(monitoring_section)
        
        return report
    except Exception as e:
        # Return a simple error report
        return {
            'title': 'Implementation Plan (Error)',
            'summary': f"An error occurred while generating the implementation plan: {str(e)}",
            'sections': [{
                'title': 'Error Details',
                'content': f"Technical details: {str(e)}"
            }],
            'conclusion': "Please try running the optimization again with different parameters."
        }

def generate_resource_assessment(input_data, current_ratios, optimization_result, include_visualizations, include_raw_data):
    """
    Generates a resource needs assessment report.
    
    Returns:
        Dictionary containing report sections
    """
    try:
        institution_name = input_data.get('institution_name', 'Your Institution')
        
        # Prepare report
        report = {
            'title': f'Resource Needs Assessment for {institution_name}',
            'summary': f"""
            This assessment provides a detailed analysis of the resources needed to implement 
            the optimized student-teacher ratio plan at {institution_name}. It identifies 
            current resource availability, gaps that need to be addressed, and recommendations 
            for efficient resource allocation.
            """,
            'sections': [],
            'conclusion': f"""
            By addressing the resource needs outlined in this assessment, {institution_name} 
            will be well-positioned to implement the optimized student-teacher ratio plan 
            successfully. Prioritizing the most critical resource gaps while taking a phased 
            approach to implementation will ensure both short-term improvements and long-term 
            sustainability of the optimization efforts.
            """
        }
        
        # Current resources section
        current_resources = {
            'title': 'Current Resource Assessment',
            'content': f"""
            {institution_name} currently has the following resources:
            
            **Human Resources:**
            - {input_data['total_teachers']} total teachers
            - Teacher distribution: {', '.join([f"{s}: {p:.1f}%" for s, p in input_data.get('teacher_distribution', {}).items()])}
            
            **Physical Resources:**
            - {input_data['num_classrooms']} classrooms
            - Maximum capacity per classroom: {input_data.get('max_class_size', 30)} students
            
            **Student Population:**
            - {input_data['total_students']} total students
            - Current overall student-teacher ratio: {current_ratios['overall']:.2f}:1
            """
        }
        
        report['sections'].append(current_resources)
        
        # Resource gaps section
        resource_gaps = {
            'title': 'Resource Gaps Analysis',
            'content': f"""
            Based on the optimization results, we've identified the following resource gaps 
            that need to be addressed:
            
            **Teacher Allocation Gaps:**
            - The optimal overall ratio is {optimization_result['optimal_ratio']:.2f}:1, which requires adjustment from the current {current_ratios['overall']:.2f}:1 ratio
            """
        }
        
        # Add subject-specific gaps if available
        if 'subject_allocation' in optimization_result and 'by_subject' in current_ratios:
            try:
                gaps = []
                for subject, details in optimization_result['subject_allocation'].items():
                    optimal = details['ratio']
                    current = current_ratios['by_subject'].get(subject, optimal)
                    difference = optimal - current
                    if abs(difference) > 0.5:  # Only show significant differences
                        gaps.append({
                            'subject': subject,
                            'current': current,
                            'optimal': optimal,
                            'difference': difference
                        })
                
                if gaps:
                    resource_gaps['content'] += "\n\n**Subject-Specific Allocation Gaps:**"
                    for gap in sorted(gaps, key=lambda x: abs(x['difference']), reverse=True):
                        direction = "decrease" if gap['difference'] < 0 else "increase"
                        resource_gaps['content'] += f"""
                        - {gap['subject']}: Need to {direction} ratio from {gap['current']:.2f}:1 to {gap['optimal']:.2f}:1"""
            except Exception:
                # Skip this part if there's an error
                pass
        
        report['sections'].append(resource_gaps)
        
        # Resource allocation strategy
        allocation_strategy = {
            'title': 'Resource Allocation Strategy',
            'content': f"""
            To address the identified resource gaps, we recommend the following allocation strategy:
            
            **Teacher Reallocation:**
            - Redistribute {input_data['total_teachers']} teachers according to the optimal allocation plan
            - Focus on ensuring adequate coverage for high-difficulty subjects
            - Maintain minimum staffing levels of at least 1 teacher per subject
            
            **Classroom Utilization:**
            - Optimize classroom usage based on the recommended allocations
            - Ensure balanced class sizes across all {input_data['num_classrooms']} classrooms
            - Maintain classroom sizes below the maximum capacity of {input_data.get('max_class_size', 30)} students
            """
        }
        
        if include_visualizations:
            try:
                # Create a visualization showing current vs. optimal allocation
                allocation_strategy['visualization'] = create_current_vs_optimal_chart(
                    current_ratios, 
                    optimization_result
                )
            except Exception:
                # Skip visualization if there's an error
                pass
        
        report['sections'].append(allocation_strategy)
        
        # Budget implications section
        budget_section = {
            'title': 'Budget Implications',
            'content': f"""
            The optimization plan is designed to work within the current resource constraints 
            of {institution_name}, minimizing additional budget requirements. However, some 
            adjustments may have budget implications:
            
            **Potential Cost-Neutral Changes:**
            - Reallocation of existing teachers across subjects and classrooms
            - Redistribution of students to achieve optimal class sizes
            - Schedule adjustments to maximize resource utilization
            
            **Potential Budget Impacts:**
            - Professional development for teachers transitioning to new subject areas
            - Administrative costs associated with implementing the new allocation plan
            - Technology or materials needed to support the optimal allocation
            
            We recommend a detailed budget review as part of the implementation planning process 
            to identify specific funding needs and potential sources.
            """
        }
        
        report['sections'].append(budget_section)
        
        # Additional resources needed
        additional_resources = {
            'title': 'Additional Resources Needed',
            'content': f"""
            Beyond the reallocation of existing resources, the following additional resources 
            may be needed to fully implement the optimization plan:
            
            **Short-term Resource Needs:**
            - Project management support for implementation coordination
            - Communication materials for stakeholder engagement
            - Data collection and analysis tools for monitoring progress
            
            **Medium-term Resource Needs:**
            - Teacher professional development in high-need subject areas
            - Classroom reconfiguration for optimal space utilization
            - Process documentation and training materials
            
            **Long-term Resource Needs:**
            - Ongoing data analysis and optimization capabilities
            - Continuous improvement resources for fine-tuning the allocation
            - Evaluation framework to assess educational outcomes
            """
        }
        
        report['sections'].append(additional_resources)
        
        # Prioritization section
        prioritization = {
            'title': 'Resource Prioritization',
            'content': f"""
            Given that not all resource needs can be addressed simultaneously, we recommend 
            the following prioritization approach:
            
            **Immediate Priorities (First 30 Days):**
            - Finalize teacher reallocation plan for critical subjects
            - Communicate changes to all stakeholders
            - Establish baseline measurements for key metrics
            
            **Short-term Priorities (First 90 Days):**
            - Complete all teacher reallocations
            - Implement classroom reassignments
            - Begin monitoring impact on educational outcomes
            
            **Medium-term Priorities (First 6 Months):**
            - Address any emerging resource gaps
            - Implement professional development for teachers
            - Refine allocation based on initial results
            
            This prioritization ensures that the most critical resource needs are addressed 
            first, while allowing for a phased approach to implementation.
            """
        }
        
        report['sections'].append(prioritization)
        
        return report
    except Exception as e:
        # Return a simple error report
        return {
            'title': 'Resource Needs Assessment (Error)',
            'summary': f"An error occurred while generating the resource assessment: {str(e)}",
            'sections': [{
                'title': 'Error Details',
                'content': f"Technical details: {str(e)}"
            }],
            'conclusion': "Please try running the optimization again with different parameters."
        }