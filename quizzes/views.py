from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer
from .serializers import (
    QuizSerializer, QuestionSerializer, ChoiceSerializer,
    QuizAttemptSerializer, StudentAnswerSerializer
)
from courses.views import IsInstructorOrReadOnly

# Create your views here.

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsInstructorOrReadOnly()]
        elif self.action in ['start_attempt', 'submit_attempt']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return Quiz.objects.filter(course_id=course_id)
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_pk')
        lesson_id = self.request.data.get('lesson_id')
        serializer.save(
            course_id=course_id,
            lesson_id=lesson_id
        )
    
    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None, course_pk=None):
        quiz = self.get_object()
        
        # Check if there's an incomplete attempt
        existing_attempt = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            completed_at__isnull=True
        ).first()
        
        if existing_attempt:
            serializer = QuizAttemptSerializer(existing_attempt)
            return Response(serializer.data)
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz
        )
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def submit_attempt(self, request, pk=None, course_pk=None):
        quiz = self.get_object()
        attempt = get_object_or_404(
            QuizAttempt,
            student=request.user,
            quiz=quiz,
            completed_at__isnull=True
        )
        
        # Process answers
        answers_data = request.data.get('answers', [])
        total_points = 0
        max_points = 0
        
        print(f"Processing quiz attempt for {request.user.username}")
        print(f"Answers received: {answers_data}")
        
        for answer_data in answers_data:
            try:
                question = get_object_or_404(Question, id=answer_data['question_id'])
                max_points += question.points
                
                print(f"Processing question {question.id}: {question.text}")
                print(f"Question points: {question.points}")
                print(f"Question type: {question.question_type}")
                
                if question.question_type in ['multiple_choice', 'true_false']:
                    try:
                        choice = Choice.objects.get(id=answer_data['choice_id'], question=question)
                        is_correct = choice.is_correct
                        
                        print(f"Selected choice ID: {choice.id}")
                        print(f"Selected choice text: {choice.text}")
                        print(f"Is correct: {is_correct}")
                        
                        if is_correct:
                            total_points += question.points
                            print(f"Points awarded: {question.points}")
                        else:
                            print("No points awarded")
                        
                        StudentAnswer.objects.create(
                            attempt=attempt,
                            question=question,
                            selected_choice=choice,
                            is_correct=is_correct
                        )
                    except Choice.DoesNotExist:
                        print(f"Error: Choice {answer_data['choice_id']} not found for question {question.id}")
                        # Create an incorrect answer if choice doesn't exist
                        StudentAnswer.objects.create(
                            attempt=attempt,
                            question=question,
                            is_correct=False
                        )
                
                elif question.question_type == 'short_answer':
                    # For short answer, instructor needs to grade manually
                    StudentAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        text_answer=answer_data['text_answer']
                    )
            except Exception as e:
                print(f"Error processing answer: {str(e)}")
                continue
        
        # Calculate score and update attempt
        score = (total_points / max_points * 100) if max_points > 0 else 0
        print(f"Final calculation: {total_points} / {max_points} * 100 = {score}")
        
        attempt.score = score
        attempt.passed = score >= quiz.passing_score
        attempt.completed_at = timezone.now()
        attempt.save()
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_pk')
        return Question.objects.filter(quiz_id=quiz_id)
    
    def perform_create(self, serializer):
        quiz = get_object_or_404(
            Quiz,
            pk=self.kwargs.get('quiz_pk'),
            course_id=self.kwargs.get('course_pk')
        )
        serializer.save(quiz=quiz)

class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        question_id = self.kwargs.get('question_pk')
        return Choice.objects.filter(question_id=question_id)
    
    def perform_create(self, serializer):
        question = get_object_or_404(
            Question,
            pk=self.kwargs.get('question_pk'),
            quiz__course_id=self.kwargs.get('course_pk')
        )
        serializer.save(question=question)

class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.userprofile.user_type == 'instructor':
            return QuizAttempt.objects.filter(
                quiz__course__instructor=self.request.user
            )
        return QuizAttempt.objects.filter(student=self.request.user)
