import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def create_current_vs_optimal_chart(current_ratios, optimization_result):
    """
    Creates a chart comparing current vs. optimal student-teacher ratios.
    
    Args:
        current_ratios: Dictionary containing current ratio information
        optimization_result: Dictionary containing optimization results
        
    Returns:
        Plotly figure object
    """
    # Overall comparison
    overall_data = pd.DataFrame({
        'Category': ['Overall'],
        'Current Ratio': [current_ratios['overall']],
        'Optimal Ratio': [optimization_result['optimal_ratio']]
    })
    
    # Subject-specific comparison
    subject_data = []
    for subject, current in current_ratios['by_subject'].items():
        if subject in optimization_result['subject_allocation']:
            optimal = optimization_result['subject_allocation'][subject]['ratio']
            subject_data.append({
                'Category': subject,
                'Current Ratio': current,
                'Optimal Ratio': optimal
            })
    
    # Combine data
    if subject_data:
        combined_data = pd.concat([overall_data, pd.DataFrame(subject_data)])
    else:
        combined_data = overall_data
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=combined_data['Category'],
        y=combined_data['Current Ratio'],
        name='Current Ratio',
        marker_color='indianred'
    ))
    
    fig.add_trace(go.Bar(
        x=combined_data['Category'],
        y=combined_data['Optimal Ratio'],
        name='Optimal Ratio',
        marker_color='royalblue'
    ))
    
    # Add horizontal line for ideal ratio
    if 'ideal_ratio' in optimization_result:
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=optimization_result['ideal_ratio'],
            x1=len(combined_data) - 0.5,
            y1=optimization_result['ideal_ratio'],
            line=dict(
                color="green",
                width=2,
                dash="dash",
            )
        )
        
        # Add annotation for ideal ratio
        fig.add_annotation(
            x=0,
            y=optimization_result['ideal_ratio'] * 1.1,
            text=f"Ideal Ratio: {optimization_result['ideal_ratio']}:1",
            showarrow=False,
            font=dict(
                color="green"
            )
        )
    
    # Update layout
    fig.update_layout(
        title='Current vs. Optimal Student-Teacher Ratios',
        xaxis_title='',
        yaxis_title='Student-Teacher Ratio',
        barmode='group',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_allocation_chart(optimization_result):
    """
    Creates a chart showing teacher and student allocation across subjects.
    
    Args:
        optimization_result: Dictionary containing optimization results
        
    Returns:
        Plotly figure object
    """
    try:
        # Extract subject allocation data
        subjects = []
        teacher_counts = []
        student_counts = []
        ratios = []
        
        for subject, details in optimization_result['subject_allocation'].items():
            subjects.append(subject)
            teacher_counts.append(details['teachers_allocated'])
            student_counts.append(details['students_allocated'])
            ratios.append(details['ratio'])
        
        # Create a simple bar chart first using px
        df = pd.DataFrame({
            'Subject': subjects,
            'Teachers': teacher_counts,
            'Students': student_counts,
            'Ratio': ratios
        })
        
        fig = px.bar(
            df, 
            x='Subject', 
            y='Students',
            title='Teacher and Student Allocation by Subject',
            labels={'Students': 'Number of Students'}
        )
        
        # Update the trace name
        fig.data[0].name = 'Students'
        fig.data[0].marker.color = 'indianred'
        
        # Add teacher bars
        teacher_bar = go.Bar(
            x=subjects,
            y=teacher_counts,
            name='Teachers',
            marker_color='royalblue',
            opacity=0.7
        )
        
        # Add ratio line
        ratio_line = go.Scatter(
            x=subjects,
            y=ratios,
            name='Ratio',
            mode='lines+markers',
            line=dict(color='green', width=3, dash='dash'),
            marker=dict(color='green', size=8)
        )
        
        # Add the new traces
        fig.add_trace(teacher_bar)
        fig.add_trace(ratio_line)
        
        # Update layout
        fig.update_layout(
            xaxis_title='Subject',
            yaxis_title='Count',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='group'
        )
        
        return fig
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Error creating chart: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Subject Allocation (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return fig

def create_heatmap(optimization_result):
    """
    Creates a heatmap showing teacher and student distribution across classrooms and subjects.
    
    Args:
        optimization_result: Dictionary containing optimization results
        
    Returns:
        Plotly figure object
    """
    try:
        # Extract data from teacher_allocation
        classrooms = set()
        subjects = set()
        data = {}
        
        for teacher in optimization_result['teacher_allocation']:
            classroom = teacher['classroom']
            subject = teacher['subject']
            students = teacher['students_assigned']
            
            classrooms.add(classroom)
            subjects.add(subject)
            
            if (classroom, subject) not in data:
                data[(classroom, subject)] = students
            else:
                data[(classroom, subject)] += students
        
        # Convert to ordered lists
        classroom_list = sorted(list(classrooms))
        subject_list = sorted(list(subjects))
        
        # Create matrix for heatmap
        matrix = []
        for classroom in classroom_list:
            row = []
            for subject in subject_list:
                row.append(data.get((classroom, subject), 0))
            matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=subject_list,
            y=classroom_list,
            colorscale='Viridis',
            text=matrix,  # Display values in the cells
            texttemplate="%{text}",
            textfont={"size": 12}
        ))
        
        fig.update_layout(
            title='Students per Subject and Classroom',
            xaxis=dict(title='Subject'),
            yaxis=dict(title='Classroom'),
            height=500
        )
        
        return fig
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Error creating heatmap: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Classroom Heatmap (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return fig

def create_recommendation_impact_chart(recommendations):
    """
    Creates a chart showing the impact of different recommendations.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Plotly figure object
    """
    try:
        # Extract data
        titles = []
        impacts = []
        ease = []
        indices = []  # For reference in text
        categories = []  # For grouping recommendations
        
        # Define categories
        category_mapping = {
            'student': 'Student-focused',
            'ratio': 'Ratio Optimization',
            'teacher': 'Teacher-focused',
            'class': 'Classroom Management',
            'resource': 'Resource Allocation',
            'schedule': 'Scheduling',
            'staff': 'Staffing'
        }
        
        for i, rec in enumerate(recommendations):
            if 'impact_score' in rec and 'ease_score' in rec:
                titles.append(rec['title'])
                impacts.append(rec['impact_score'])
                ease.append(rec['ease_score'])
                indices.append(i+1)  # 1-based indexing for display
                
                # Determine category based on title keywords
                title_lower = rec['title'].lower()
                category = 'Other'
                for key, value in category_mapping.items():
                    if key in title_lower:
                        category = value
                        break
                categories.append(category)
        
        # Create dataframe for easier handling
        df = pd.DataFrame({
            'Title': titles,
            'Impact': impacts,
            'Ease': ease,
            'Index': indices,
            'Category': categories
        })
        
        # Create a horizontal bar chart that's easier to read than scatter plot
        fig = go.Figure()
        
        # Sort by impact score
        df = df.sort_values('Impact', ascending=True)
        
        # Add bars with colors based on ease of implementation
        for i, row in df.iterrows():
            # Scale colors based on ease (green for easy, red for difficult)
            ease_color = f'rgba({255-int(row["Ease"]*25.5)}, {int(row["Ease"]*25.5)}, 0, 0.8)'
            
            # Add bar
            fig.add_trace(go.Bar(
                y=[f"{row['Index']}. {row['Title']}"],
                x=[row['Impact']],
                orientation='h',
                name=row['Category'],
                marker=dict(
                    color=ease_color,
                    line=dict(color='rgba(0, 0, 0, 0.5)', width=1)
                ),
                text=f"Impact: {row['Impact']}/10<br>Ease: {row['Ease']}/10<br>Category: {row['Category']}",
                hoverinfo='text',
                textposition='auto'
            ))
        
        # Add a legend for ease of implementation
        fig.add_annotation(
            x=0,
            y=-0.15,
            xref="paper",
            yref="paper",
            text="Color indicates ease of implementation: <span style='color:red'>⬤</span> Difficult → <span style='color:orange'>⬤</span> Moderate → <span style='color:green'>⬤</span> Easy",
            showarrow=False,
            font=dict(size=12),
            align="left"
        )
        
        # Add impact level indicators
        fig.add_shape(
            type="line",
            x0=3.3, y0=-0.5,
            x1=3.3, y1=len(df)-0.5,
            line=dict(color="red", width=1, dash="dash")
        )
        
        fig.add_shape(
            type="line",
            x0=6.7, y0=-0.5,
            x1=6.7, y1=len(df)-0.5,
            line=dict(color="green", width=1, dash="dash")
        )
        
        # Add impact level labels
        fig.add_annotation(
            x=1.65,
            y=len(df) + 0.5,
            text="LOW IMPACT",
            showarrow=False,
            font=dict(size=10, color="red")
        )
        
        fig.add_annotation(
            x=5,
            y=len(df) + 0.5,
            text="MEDIUM IMPACT",
            showarrow=False,
            font=dict(size=10, color="orange")
        )
        
        fig.add_annotation(
            x=8.35,
            y=len(df) + 0.5,
            text="HIGH IMPACT",
            showarrow=False,
            font=dict(size=10, color="green")
        )
        
        # Update layout for better appearance
        fig.update_layout(
            title={
                'text': 'Recommendation Impact Analysis',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis=dict(
                title='Impact Score (1-10)',
                range=[0, 10],
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title='',
                autorange="reversed"  # To show highest impact at the top
            ),
            height=400 + (len(df) * 30),  # Dynamic height based on number of recommendations
            margin=dict(l=20, r=20, t=80, b=80),
            plot_bgcolor='rgba(245, 245, 245, 0.8)',
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Error creating recommendation chart: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Recommendation Impact Analysis (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return fig

def create_alternate_recommendation_chart(recommendations):
    """
    Creates an alternate chart showing recommendations grouped by category.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Plotly figure object
    """
    try:
        # Process recommendations
        categories = {
            'Quick Wins': [],
            'Major Projects': [],
            'Fill-In Tasks': [],
            'Low Priority': []
        }
        
        for i, rec in enumerate(recommendations):
            if 'impact_score' in rec and 'ease_score' in rec:
                # Determine quadrant
                impact = rec['impact_score']
                ease = rec['ease_score']
                
                if impact >= 5 and ease >= 5:
                    category = 'Quick Wins'
                elif impact >= 5 and ease < 5:
                    category = 'Major Projects'
                elif impact < 5 and ease < 5:
                    category = 'Fill-In Tasks'
                else:  # impact < 5 and ease >= 5
                    category = 'Low Priority'
                
                # Add to category with index
                categories[category].append({
                    'index': i+1,
                    'title': rec['title'],
                    'impact': impact,
                    'ease': ease
                })
        
        # Prepare data for treemap
        data = []
        for category, items in categories.items():
            if items:
                for item in items:
                    data.append({
                        'Category': category,
                        'Recommendation': item['title'],
                        'Impact': item['impact'],
                        'Ease': item['ease'],
                        'Size': item['impact'] * item['ease']  # Size based on impact * ease
                    })
        
        # Use a horizontal bar chart with grouped bars instead of treemap
        if not data:
            # Create empty plot with message if no data
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No recommendation data available",
                showarrow=False
            )
            fig.update_layout(
                title="Recommendation Categories",
                height=400
            )
            return fig
            
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(data)
        
        # Sort by category and impact score
        df = df.sort_values(['Category', 'Impact'], ascending=[True, False])
        
        # Create a grouped bar chart 
        fig = px.bar(
            df,
            y='Recommendation',
            x='Impact',
            color='Category',
            color_discrete_map={
                'Quick Wins': '#2ca02c',      # Green
                'Major Projects': '#ff7f0e',  # Orange
                'Fill-In Tasks': '#1f77b4',   # Blue
                'Low Priority': '#d62728'     # Red
            },
            orientation='h',
            text='Impact',
            height=max(400, len(df) * 30),  # Dynamic height based on number of recommendations
            labels={'Impact': 'Impact Score', 'Recommendation': ''},
            title="Recommendations by Category"
        )
        
        # Update layout for better appearance
        fig.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            yaxis=dict(automargin=True),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Error creating recommendation chart: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Recommendation Categories (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return fig

def create_classroom_balance_chart(optimization_result):
    """
    Creates a chart showing the balance of students and teachers across classrooms.
    
    Args:
        optimization_result: Dictionary containing optimization results
        
    Returns:
        Plotly figure object
    """
    try:
        # Extract classroom data
        classroom_ids = []
        teacher_counts = []
        student_counts = []
        ratios = []
        
        for i, classroom in enumerate(optimization_result['classroom_allocation']):
            classroom_ids.append(f"Classroom {i+1}")
            teacher_counts.append(classroom['teachers_assigned'])
            student_counts.append(classroom['students_assigned'])
            ratios.append(classroom['ratio'])
        
        # Create dataframe for easier plotting
        df = pd.DataFrame({
            'Classroom': classroom_ids,
            'Teachers': teacher_counts,
            'Students': student_counts,
            'Ratio': ratios
        })
        
        # Create a grouped bar chart
        fig = px.bar(
            df,
            x='Classroom',
            y=['Teachers', 'Students'],
            barmode='group',
            labels={'value': 'Count', 'variable': 'Type'},
            title='Classroom Balance Analysis',
            color_discrete_map={'Teachers': 'royalblue', 'Students': 'indianred'}
        )
        
        # Add ratio line on secondary y-axis
        ratio_line = go.Scatter(
            x=classroom_ids,
            y=ratios,
            name='Ratio',
            mode='lines+markers',
            line=dict(color='green', width=3),
            marker=dict(size=8),
            yaxis='y2'
        )
        
        fig.add_trace(ratio_line)
        
        # Add optimal ratio reference line
        optimal_ratio = optimization_result.get('optimal_ratio', sum(ratios)/len(ratios) if ratios else 0)
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=optimal_ratio,
            x1=len(classroom_ids) - 0.5,
            y1=optimal_ratio,
            line=dict(color="green", width=2, dash="dash"),
            yaxis='y2'
        )
        
        # Add annotation for optimal ratio
        fig.add_annotation(
            x=0,
            y=optimal_ratio * 1.1,
            text=f"Optimal Ratio: {optimal_ratio:.2f}:1",
            showarrow=False,
            font=dict(color="green"),
            yshift=10,
            yref='y2'
        )
        
        # Update layout with secondary y-axis
        fig.update_layout(
            xaxis_title='Classroom',
            yaxis_title='Count',
            yaxis2=dict(
                title='Ratio',
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(ratios) * 1.2] if ratios else [0, 10]
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        # Create a simple fallback chart if there's an error
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Error creating classroom balance chart: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title='Classroom Balance Analysis (Error)',
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        return fig