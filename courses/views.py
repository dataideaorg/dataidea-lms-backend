from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, Section, Lesson, Enrollment, LessonProgress, Bookmark
from .serializers import (
    CourseSerializer, SectionSerializer, LessonSerializer,
    EnrollmentSerializer, LessonProgressSerializer, BookmarkSerializer
)

# Create your views here.

class IsInstructorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.userprofile.user_type == 'instructor'

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsInstructorOrReadOnly()]
        elif self.action == 'enroll':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = Course.objects.all()
        if self.request.user.userprofile.user_type != 'instructor':
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        
        # Check if the course is published (only for students)
        if request.user.userprofile.user_type != 'instructor' and not course.is_published:
            return Response(
                {'error': 'This course is not available for enrollment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'error': 'Already enrolled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return Section.objects.filter(course_id=course_id)
    
    def perform_create(self, serializer):
        course = get_object_or_404(Course, pk=self.kwargs.get('course_pk'))
        serializer.save(course=course)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['mark_complete']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def get_queryset(self):
        section_id = self.kwargs.get('section_pk')
        return Lesson.objects.filter(section_id=section_id)
    
    def perform_create(self, serializer):
        section = get_object_or_404(Section, pk=self.kwargs.get('section_pk'))
        serializer.save(section=section)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None, section_pk=None, course_pk=None):
        lesson = self.get_object()
        course = lesson.section.course
        
        # Check if user is enrolled in the course
        if not course.enrollments.filter(student=request.user).exists():
            return Response(
                {'error': 'You must be enrolled in this course to mark lessons as complete'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson,
            defaults={'completed': True}
        )
        if not created:
            progress.completed = True
            progress.save()
        
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'])
    def bookmark(self, request, pk=None, section_pk=None, course_pk=None):
        lesson = self.get_object()
        
        if request.method == 'POST':
            bookmark, created = Bookmark.objects.get_or_create(
                student=request.user,
                lesson=lesson,
                defaults={'note': request.data.get('note', '')}
            )
            if not created and 'note' in request.data:
                bookmark.note = request.data['note']
                bookmark.save()
            
            serializer = BookmarkSerializer(bookmark)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            bookmark = get_object_or_404(Bookmark, student=request.user, lesson=lesson)
            bookmark.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.userprofile.user_type == 'instructor':
            return Enrollment.objects.filter(course__instructor=self.request.user).select_related(
                'student', 'course', 'course__instructor'
            ).prefetch_related(
                'course__sections',
                'course__sections__lessons',
                'course__sections__student_progress',
                'course__sections__lessons__student_progress'
            )
        return Enrollment.objects.filter(student=self.request.user).select_related(
            'student', 'course', 'course__instructor'
        ).prefetch_related(
            'course__sections',
            'course__sections__lessons',
            'course__sections__student_progress',
            'course__sections__lessons__student_progress'
        )

class LessonProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.userprofile.user_type == 'instructor':
            return LessonProgress.objects.filter(lesson__section__course__instructor=self.request.user)
        return LessonProgress.objects.filter(student=self.request.user)

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(student=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
