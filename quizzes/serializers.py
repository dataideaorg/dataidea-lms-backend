from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer
from courses.serializers import CourseSerializer, LessonSerializer
from accounts.serializers import UserSerializer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'text', 'is_correct')
        read_only_fields = ('id',)
        extra_kwargs = {'is_correct': {'write_only': True}}  # Hide correct answer from students

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'question_type', 'text', 'order', 'points', 'choices')
        read_only_fields = ('id',)

class QuizSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    total_points = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'course', 'lesson', 'passing_score',
                 'created_at', 'updated_at', 'questions', 'total_points')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_total_points(self, obj):
        return sum(question.points for question in obj.questions.all())

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ('id', 'question', 'selected_choice', 'text_answer', 'is_correct')
        read_only_fields = ('id', 'is_correct')

class QuizAttemptSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    quiz = QuizSerializer(read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ('id', 'student', 'quiz', 'score', 'started_at', 'completed_at',
                 'passed', 'answers')
        read_only_fields = ('id', 'score', 'started_at', 'completed_at', 'passed') 