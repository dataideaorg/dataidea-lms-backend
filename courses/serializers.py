from rest_framework import serializers
from .models import Course, Section, Lesson, Enrollment, LessonProgress, SectionProgress, Bookmark
from accounts.serializers import UserSerializer

class BookmarkLessonSerializer(serializers.ModelSerializer):
    section = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'section')
    
    def get_section(self, obj):
        return {
            'id': obj.section.id,
            'title': obj.section.title,
            'course': {
                'id': obj.section.course.id,
                'title': obj.section.course.title
            }
        }

class BookmarkSerializer(serializers.ModelSerializer):
    lesson = BookmarkLessonSerializer(read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ('id', 'lesson', 'created_at', 'note')
        read_only_fields = ('id', 'created_at')

class LessonSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content', 'video_url', 'order', 'duration',
                 'created_at', 'updated_at', 'status', 'is_bookmarked')
        read_only_fields = ('id', 'created_at', 'updated_at', 'status', 'is_bookmarked')
    
    def get_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_status(request.user)
        return 'not_started'
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(student=request.user).exists()
        return False

class SectionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionProgress
        fields = ('id', 'completed', 'progress', 'last_accessed')
        read_only_fields = ('id', 'last_accessed')

class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ('id', 'title', 'order', 'lessons', 'progress')
        read_only_fields = ('id', 'progress')
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_progress(request.user)
        return 0

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    sections = SectionSerializer(many=True, read_only=True)
    enrolled_students_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ('id', 'title', 'description', 'instructor', 'thumbnail', 
                 'created_at', 'updated_at', 'is_published', 'sections',
                 'enrolled_students_count', 'progress', 'is_enrolled')
        read_only_fields = ('id', 'created_at', 'updated_at', 'progress', 'is_enrolled')
    
    def get_enrolled_students_count(self, obj):
        return obj.enrollments.count()
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_progress(request.user)
        return 0
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user).exists()
        return False

class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'course', 'enrolled_at', 'completed',
                 'last_accessed', 'progress')
        read_only_fields = ('id', 'enrolled_at', 'last_accessed', 'progress')

class LessonProgressSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = ('id', 'student', 'lesson', 'completed', 'last_accessed')
        read_only_fields = ('id', 'last_accessed') 