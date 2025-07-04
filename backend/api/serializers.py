# backend/api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User, Group # Import Group
from .models import Course, Enrollment, Assignment, Grade
from dj_rest_auth.serializers import UserDetailsSerializer # Import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer

# --- Custom User Details Serializer for dj-rest-auth ---
class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Custom UserDetailsSerializer to include group names.
    This will be used by dj-rest-auth's /api/auth/user/ endpoint.
    """
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'  # We want the group name, e.g., "Students", "Teachers"
    )

    class Meta(UserDetailsSerializer.Meta):
        # UserDetailsSerializer.Meta.fields already includes basic user fields like:
        # pk, username, email, first_name, last_name
        # We add 'groups' to this list.
        fields = UserDetailsSerializer.Meta.fields + ('groups',)

# --- Your Existing Serializers ---

# Serializer for Course model
class CourseSerializer(serializers.ModelSerializer):
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='teacher', 
        write_only=True, 
        required=False, # Make it not strictly required if a course can exist without a teacher initially
        allow_null=True   # Or if a course can explicitly have no teacher
    )
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'teacher_id', 'teacher_username']

# Serializer for Assignment model
class AssignmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    # course_name = serializers.CharField(source='course.name', read_only=True) # Optional: if you also want course name

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'course_code', 'title', 'description', 'due_date', 'total_points']
        read_only_fields = ['course_code'] 
        extra_kwargs = {
            'course': {'write_only': True} 
        }

# Serializer for Grade model
class GradeSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    course_code = serializers.CharField(source='assignment.course.code', read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id',
            'assignment', 
            'student',    
            'assignment_title',
            'student_username',
            'course_code',
            'score',
            'submission_status',
            'submitted_at',
            'feedback'
        ]
        read_only_fields = ['student_username', 'assignment_title', 'course_code']
        extra_kwargs = {
            'assignment': {'write_only': True},
            # Student is often set based on the authenticated user, especially for student submissions
            'student': {'write_only': True, 'required': False} 
        }

# Serializer specifically for listing courses a student is enrolled in
class StudentEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True) # Nest the full course details

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrollment_date']

# --- Optional: Basic User Serializer (if needed elsewhere, not for dj-rest-auth user details) ---
# This is now largely superseded by CustomUserDetailsSerializer for the /api/auth/user/ endpoint.
# You might still use it if you have other API endpoints that need a simpler user representation.
class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

# --- CUSTOM REGISTRATION SERIALIZER ---

class CustomRegisterSerializer(RegisterSerializer):
    ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Educator', 'Educator'), # "Educator" in UI maps to "Teachers" group in backend
    )
    # Add a 'role' field to the serializer. This will be sent from Streamlit.
    role = serializers.ChoiceField(choices=ROLE_CHOICES, write_only=True)

    def save(self, request):
        # Call the parent save() method to create the user
        user = super().save(request)
        
        # Get the role from validated_data
        selected_role = self.validated_data.get('role')
        
        if selected_role == 'Student':
            group_name = 'Students'
        elif selected_role == 'Educator':
            group_name = 'Teachers'
        else:
            # Optional: handle if role is somehow invalid or not provided,
            # though ChoiceField should validate it.
            # Or assign a default group, or raise an error.
            # For now, we assume valid input from ChoiceField.
            return user # Or raise serializers.ValidationError("Invalid role selected.")

        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            # This should not happen if you've created "Students" and "Teachers" groups.
            # You might want to log this error.
            print(f"ERROR: Group '{group_name}' does not exist. User '{user.username}' not added to group.")
            # Optionally, you could raise a validation error to inform the user/admin
            # raise serializers.ValidationError(f"Configuration error: Role group '{group_name}' not found.")
        
        return user