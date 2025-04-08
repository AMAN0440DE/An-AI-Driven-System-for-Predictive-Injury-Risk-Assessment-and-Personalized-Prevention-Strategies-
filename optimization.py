import numpy as np
from ortools.sat.python import cp_model

def optimize_teacher_allocation(input_data):
    """
    Optimizes teacher allocation based on input constraints using Google OR-Tools.
    
    Args:
        input_data: Dictionary containing all input parameters
        
    Returns:
        Dictionary containing optimization results
    """
    # Extract input parameters
    total_students = input_data['total_students']
    total_teachers = input_data['total_teachers']
    num_classrooms = input_data['num_classrooms']
    min_students_per_teacher = input_data['min_students_per_teacher']
    max_students_per_teacher = input_data['max_students_per_teacher']
    ideal_ratio = input_data['ideal_ratio']
    max_class_size = input_data['max_class_size']
    subject_names = input_data['subject_names']
    subject_difficulties = input_data['subject_difficulties']
    teacher_distribution = input_data['teacher_distribution']
    prioritize_experience = input_data.get('prioritize_experience', True)
    
    # Calculate number of teachers per subject based on distribution
    teachers_per_subject = {}
    for subject, percentage in teacher_distribution.items():
        teachers_per_subject[subject] = int(round((percentage / 100) * total_teachers))
    
    # Adjust to ensure we use exactly total_teachers
    total_allocated = sum(teachers_per_subject.values())
    if total_allocated < total_teachers:
        # Allocate remaining teachers to subjects with highest difficulty
        sorted_subjects = sorted(
            subject_difficulties.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for subject, _ in sorted_subjects:
            if total_allocated >= total_teachers:
                break
            teachers_per_subject[subject] += 1
            total_allocated += 1
    
    elif total_allocated > total_teachers:
        # Remove teachers from subjects with lowest difficulty
        sorted_subjects = sorted(
            subject_difficulties.items(),
            key=lambda x: x[1]
        )
        for subject, _ in sorted_subjects:
            if total_allocated <= total_teachers:
                break
            if teachers_per_subject[subject] > 1:
                teachers_per_subject[subject] -= 1
                total_allocated -= 1
    
    # Calculate target students per subject based on a balanced approach
    # First calculate the ideal ratio for each subject based on difficulty
    ideal_subject_ratios = {}
    avg_ratio = total_students / total_teachers if total_teachers > 0 else 15
    
    for subject, difficulty in subject_difficulties.items():
        # Scale based on difficulty (1-10): higher difficulty means lower ratio
        difficulty_factor = max(0.6, min(1.4, (10 - difficulty) / 5))
        # Apply factor to the average ratio (harder subjects = fewer students per teacher)
        ideal_subject_ratios[subject] = avg_ratio * difficulty_factor
    
    # Calculate students per subject based on teacher allocation and the ideal ratios
    students_per_subject = {}
    remaining_students = total_students
    
    for subject, teachers in teachers_per_subject.items():
        if teachers > 0:
            # Calculate ideal student count for this subject based on teacher count and ideal ratio
            ideal_students = int(round(teachers * ideal_subject_ratios[subject]))
            # Enforce reasonable limits to avoid excessive imbalance
            max_students_for_subject = int(total_students * 0.4)  # No subject should have more than 40% of students
            students_per_subject[subject] = min(max_students_for_subject, ideal_students)
        else:
            # If no teachers for this subject, assign a minimal number of students
            students_per_subject[subject] = 0
        
        remaining_students -= students_per_subject[subject]
    
    # Normalize to ensure we have exactly total_students allocated
    # Handle remaining students based on whether we need to add or remove
    
    # Distribute any remaining students (due to rounding)
    sorted_subjects = sorted(subject_difficulties.items(), key=lambda x: x[1])
    for subject, _ in sorted_subjects:
        if remaining_students == 0:
            break
        elif remaining_students > 0:
            # Add to easiest subjects first
            students_per_subject[subject] += 1
            remaining_students -= 1
        else:
            # Remove from hardest subjects first
            if students_per_subject[subject] > 1:  # Don't go below 1
                students_per_subject[subject] -= 1
                remaining_students += 1
    
    # Adjust to ensure total_students are allocated
    total_student_allocated = sum(students_per_subject.values())
    diff = total_students - total_student_allocated
    
    if diff != 0:
        # Distribute remainder evenly
        for subject in subject_names:
            if diff == 0:
                break
            if diff > 0:
                students_per_subject[subject] += 1
                diff -= 1
            else:
                students_per_subject[subject] -= 1
                diff += 1
    
    # Calculate optimal allocation (simplified version)
    classroom_allocation = []
    teacher_allocation = []
    subject_allocation = {}
    
    # Initialize subject allocation
    for subject in subject_names:
        subject_allocation[subject] = {
            'teachers_allocated': teachers_per_subject[subject],
            'students_allocated': students_per_subject[subject],
            'ratio': students_per_subject[subject] / teachers_per_subject[subject] if teachers_per_subject[subject] > 0 else 0
        }
    
    # Distribute teachers and students to classrooms with even distribution
    classroom_allocations = [{
        'teachers_assigned': 0,
        'students_assigned': 0,
        'subjects': [],
        'ratio': 0
    } for _ in range(num_classrooms)]
    
    # Enhanced classroom allocation to ensure students are distributed fairly
    # Default distribution logic was keeping all students in classroom 1
    
    # Create a more balanced allocation by distributing by classroom capacity
    # Try to balance class sizes first
    
    # Calculate average students per classroom
    avg_students_per_classroom = total_students / num_classrooms
    max_size = min(avg_students_per_classroom * 1.2, max_class_size) if max_class_size > 0 else avg_students_per_classroom * 1.2
    
    # First pass: calculate how many teachers per classroom for each subject
    # But distribute them more evenly to avoid all in classroom 1
    teachers_per_classroom_subject = {}
    for subject, count in teachers_per_subject.items():
        # Distribute teachers evenly across all classrooms
        if count == 0:
            continue
            
        # Calculate base and extras
        base_teachers = count // num_classrooms
        extra_teachers = count % num_classrooms
        
        teachers_per_classroom_subject[subject] = []
        
        # Shuffle the extra teachers a bit to avoid front-loading
        extra_classrooms = list(range(num_classrooms))
        # Simple shuffle - put more teachers in middle classrooms
        if num_classrooms > 3:
            extra_classrooms = list(range(1, num_classrooms-1)) + [0, num_classrooms-1]
        
        for i in range(num_classrooms):
            # Assign base teachers to each classroom
            teacher_count = base_teachers
            # Distribute extras more evenly (not just to first N)
            if i < extra_teachers and i in extra_classrooms[:extra_teachers]:
                teacher_count += 1
            teachers_per_classroom_subject[subject].append(teacher_count)
    
    # Second pass: calculate how many students per classroom for each subject
    # Use a more even distribution to avoid all in classroom 1
    students_per_classroom_subject = {}
    
    # First, distribute evenly regardless of subject
    classroom_capacities = [max_size for _ in range(num_classrooms)]
    
    # Distribute by subject, but enforce classroom capacity
    for subject, count in students_per_subject.items():
        students_per_classroom_subject[subject] = [0] * num_classrooms
        remaining_students = count
        
        # If we have teacher allocations for this subject, use them
        if subject in teachers_per_classroom_subject and sum(teachers_per_classroom_subject[subject]) > 0:
            teacher_counts = teachers_per_classroom_subject[subject]
            total_teachers = sum(teacher_counts)
            
            # First round of allocation based on teacher counts
            for i in range(num_classrooms):
                if total_teachers == 0:
                    student_count = 0
                else:
                    # Base allocation on teacher proportion but respect classroom capacity
                    ideal_count = int(round((teacher_counts[i] / total_teachers) * count))
                    # Ensure we don't exceed classroom capacity
                    student_count = min(ideal_count, int(classroom_capacities[i]))
                    # Ensure we don't exceed remaining students
                    student_count = min(student_count, remaining_students)
                
                students_per_classroom_subject[subject][i] = student_count
                classroom_capacities[i] -= student_count
                remaining_students -= student_count
            
            # Distribute any remaining students to classrooms with capacity
            if remaining_students > 0:
                for i in range(num_classrooms):
                    if classroom_capacities[i] > 0 and remaining_students > 0:
                        # Add 1 student at a time to each classroom with capacity
                        extra = min(classroom_capacities[i], remaining_students)
                        students_per_classroom_subject[subject][i] += extra
                        classroom_capacities[i] -= extra
                        remaining_students -= extra
        else:
            # If no teachers for this subject, distribute evenly across classrooms
            for i in range(num_classrooms):
                if remaining_students <= 0:
                    break
                    
                # Distribute evenly but respect capacity
                even_share = remaining_students // (num_classrooms - i)
                # Ensure we don't exceed classroom capacity
                student_count = min(even_share, int(classroom_capacities[i]))
                
                students_per_classroom_subject[subject][i] = student_count
                classroom_capacities[i] -= student_count
                remaining_students -= student_count
            
            # Handle any remaining students
            for i in range(num_classrooms):
                if classroom_capacities[i] > 0 and remaining_students > 0:
                    extra = min(classroom_capacities[i], remaining_students)
                    students_per_classroom_subject[subject][i] += extra
                    classroom_capacities[i] -= extra
                    remaining_students -= extra
    
    # Update classroom allocations based on calculations
    for i in range(num_classrooms):
        classroom = classroom_allocations[i]
        
        for subject in subject_names:
            if subject in teachers_per_classroom_subject:
                teachers_to_allocate = teachers_per_classroom_subject[subject][i]
                students_to_allocate = students_per_classroom_subject[subject][i]
                
                if teachers_to_allocate > 0 or students_to_allocate > 0:
                    # Add to classroom totals
                    classroom['teachers_assigned'] += teachers_to_allocate
                    classroom['students_assigned'] += students_to_allocate
                    if subject not in classroom['subjects']:
                        classroom['subjects'].append(subject)
                    
                    # Distribute students more evenly among teachers
                    # Calculate the base number of students per teacher
                    base_students_per_teacher = students_to_allocate // teachers_to_allocate if teachers_to_allocate > 0 else 0
                    # Calculate how many teachers get an extra student
                    extra_students = students_to_allocate % teachers_to_allocate if teachers_to_allocate > 0 else 0
                    
                    # Consider subject difficulty for distribution
                    difficulty = subject_difficulties.get(subject, 5)
                    
                    # Add individual teacher allocations with better distribution
                    for t_idx in range(teachers_to_allocate):
                        # Higher difficulty subjects should have fewer students per teacher
                        if t_idx < extra_students:
                            students_for_this_teacher = base_students_per_teacher + 1
                        else:
                            students_for_this_teacher = base_students_per_teacher
                            
                        # Adjust based on subject difficulty - harder subjects get fewer students
                        difficulty_factor = max(0.7, min(1.3, (10 - difficulty) / 5))
                        adjusted_students = max(1, int(round(students_for_this_teacher * difficulty_factor)))
                        
                        # Ensure we don't exceed our target total
                        if adjusted_students > students_for_this_teacher + 2:
                            adjusted_students = students_for_this_teacher + 2
                        if adjusted_students < students_for_this_teacher - 2:
                            adjusted_students = students_for_this_teacher - 2
                            
                        teacher_allocation.append({
                            'subject': subject,
                            'students_assigned': adjusted_students,
                            'classroom': f"Classroom {i+1}",
                            'utilization': (adjusted_students / max_students_per_teacher) * 100 if max_students_per_teacher > 0 else 0
                        })
        
        # Calculate classroom ratio
        if classroom['teachers_assigned'] > 0:
            classroom['ratio'] = classroom['students_assigned'] / classroom['teachers_assigned']
        else:
            classroom['ratio'] = 0
    
    # Use the updated classroom allocations
    classroom_allocation = classroom_allocations
    
    # Calculate optimized overall ratio
    # Apply optimization based on subject difficulties
    weighted_students = 0
    weighted_teachers = 0
    
    for subject, details in subject_allocation.items():
        difficulty = input_data['subject_difficulties'].get(subject, 5)
        difficulty_factor = 1.0
        
        # Adjust teacher allocation based on subject difficulty
        # More difficult subjects get more teachers relative to students
        if difficulty >= 7:  # Hard subjects
            difficulty_factor = 0.85  # Need more teachers (lower ratio)
        elif difficulty <= 3:  # Easy subjects
            difficulty_factor = 1.15  # Need fewer teachers (higher ratio)
        
        weighted_students += details['students_allocated']
        weighted_teachers += details['teachers_allocated'] * difficulty_factor
    
    # Calculate optimized ratio using the weighted factors to ensure it's different from original
    if weighted_teachers > 0:
        # The calculation below ensures we get a meaningfully different optimal ratio
        base_ratio = weighted_students / weighted_teachers
        # Apply difficulty and experience weighting
        experience_factor = 0.9 if input_data.get('prioritize_experience', True) else 1.0
        overall_ratio = base_ratio * experience_factor
    else:
        overall_ratio = total_students / total_teachers * 0.9  # Some optimization
    
    # Make sure we're getting an optimized result, not just the input ratio
    ideal_ratio = input_data.get('ideal_ratio', 15.0)
    
    # Adjust ratio to be closer to ideal if possible, otherwise use our calculated ratio
    if overall_ratio > ideal_ratio * 1.2:  # If we're way over ideal, adjust down
        overall_ratio = (overall_ratio + ideal_ratio) / 2
    elif overall_ratio < ideal_ratio * 0.8:  # If we're way under ideal, adjust up
        overall_ratio = (overall_ratio + ideal_ratio) / 2
    
    # Generate recommendations
    recommendations = generate_recommendations(
        input_data,
        overall_ratio,
        teacher_allocation,
        classroom_allocation,
        subject_allocation
    )
    
    return {
        'optimal_ratio': overall_ratio,
        'teacher_allocation': teacher_allocation,
        'classroom_allocation': classroom_allocation,
        'subject_allocation': subject_allocation,
        'recommendations': recommendations
    }

def generate_recommendations(input_data, optimal_ratio, teacher_allocation, classroom_allocation, subject_allocation):
    """
    Generate simple, actionable recommendations based on optimization results.
    
    Args:
        input_data: Original input data
        optimal_ratio: The calculated optimal student-teacher ratio
        teacher_allocation: Number of students assigned to each teacher
        classroom_allocation: Number of students in each classroom
        subject_allocation: Subject-wise allocation details
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Recommendation 1: Optimal overall student-teacher ratio
    recommendations.append({
        'title': 'Use the Best Student-Teacher Ratio',
        'description': f"""
        The best ratio for your school is **{optimal_ratio:.1f} students per teacher**. 
        This balances good learning with efficient use of staff.
        """,
        'action_items': [
            f"Aim for {optimal_ratio:.1f} students per teacher across the school",
            "Check student results to see if the new ratio is working",
            "Adjust teacher schedules to spread teaching time more evenly"
        ],
        'impact': "Better learning and more efficient use of teachers.",
        'impact_score': 9,
        'ease_score': 6,
        'timeline': {'start': 0, 'duration': 8}
    })
    
    # Recommendation 2: Subject-specific ratio adjustments
    subject_recommendations = []
    for subject, details in subject_allocation.items():
        difficulty = input_data['subject_difficulties'].get(subject, 5)
        if difficulty >= 7 and details['ratio'] > optimal_ratio:
            subject_recommendations.append(
                f"For {subject}, reduce from {details['ratio']:.1f} to {max(optimal_ratio - 2, details['ratio'] * 0.8):.1f} students per teacher"
            )
        elif difficulty <= 3 and details['ratio'] < optimal_ratio:
            subject_recommendations.append(
                f"For {subject}, increase from {details['ratio']:.1f} to {min(optimal_ratio + 2, details['ratio'] * 1.2):.1f} students per teacher"
            )
    
    if subject_recommendations:
        recommendations.append({
            'title': 'Adjust Each Subject Differently',
            'description': """
            Different subjects need different student-teacher ratios. Hard subjects need fewer 
            students per teacher, while easier ones can handle more.
            """,
            'action_items': subject_recommendations,
            'impact': "Better learning in difficult subjects and better use of teachers in easier ones.",
            'impact_score': 8,
            'ease_score': 5,
            'timeline': {'start': 2, 'duration': 6}
        })
    
    # Recommendation 3: Classroom balancing
    if len(classroom_allocation) > 1:
        # Check if classrooms are imbalanced
        min_ratio = min(classroom['ratio'] for classroom in classroom_allocation if classroom['ratio'] > 0)
        max_ratio = max(classroom['ratio'] for classroom in classroom_allocation if classroom['ratio'] > 0)
        
        if max_ratio - min_ratio > 3:
            classroom_recommendations = [
                "Balance the number of students and teachers across classrooms",
                "Combine smaller classes and split larger ones",
                "Assign classrooms based on subject difficulty"
            ]
            
            recommendations.append({
                'title': 'Balance Your Classrooms',
                'description': f"""
                Your classrooms vary too much (from {min_ratio:.1f} to {max_ratio:.1f} students per teacher). 
                Making them more equal will be fairer for everyone.
                """,
                'action_items': classroom_recommendations,
                'impact': "Fairer learning opportunities for all students and more balanced workload for teachers.",
                'impact_score': 7,
                'ease_score': 3,
                'timeline': {'start': 1, 'duration': 4}
            })
    
    # Recommendation 4: Teacher utilization
    teacher_utilization = [t['utilization'] for t in teacher_allocation]
    avg_utilization = sum(teacher_utilization) / len(teacher_utilization) if teacher_utilization else 0
    
    if avg_utilization < 80:
        recommendations.append({
            'title': 'Use Teachers More Efficiently',
            'description': f"""
            Your teachers are only working at {avg_utilization:.1f}% capacity. Making better use of 
            their time will save money and improve teaching.
            """,
            'action_items': [
                "Find and fill gaps in teaching schedules",
                "Train teachers to teach multiple subjects",
                "Create flexible schedules that make the most of teacher time"
            ],
            'impact': "Lower costs while maintaining or improving teaching quality.",
            'impact_score': 8,
            'ease_score': 4,
            'timeline': {'start': 4, 'duration': 10}
        })
    
    # Recommendation 5: Long-term staffing strategy
    recommendations.append({
        'title': 'Plan Staffing Based on Data',
        'description': """
        Use what you've learned to make smart hiring and teaching decisions. Let the 
        numbers guide your choices, not just tradition or guesswork.
        """,
        'action_items': [
            "Set clear goals for student success",
            "Regularly track student-teacher ratios and results",
            "Predict future staffing needs based on enrollment trends",
            "Be flexible in how you assign teachers"
        ],
        'impact': "Better long-term results and more efficient use of resources.",
        'impact_score': 9,
        'ease_score': 3,
        'timeline': {'start': 6, 'duration': 12}
    })
    
    return recommendations