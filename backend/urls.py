"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_nested import routers
from accounts.views import UserViewSet, UserProfileViewSet
from courses.views import (
    CourseViewSet, SectionViewSet, LessonViewSet,
    EnrollmentViewSet, LessonProgressViewSet
)
from quizzes.views import (
    QuizViewSet, QuestionViewSet, ChoiceViewSet,
    QuizAttemptViewSet
)

# Create the main router
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'progress', LessonProgressViewSet, basename='progress')

# Create nested routers for course-related endpoints
courses_router = routers.NestedDefaultRouter(router, r'courses', lookup='course')
courses_router.register(r'sections', SectionViewSet, basename='course-sections')
courses_router.register(r'quizzes', QuizViewSet, basename='course-quizzes')

# Create nested routers for section-related endpoints
sections_router = routers.NestedDefaultRouter(courses_router, r'sections', lookup='section')
sections_router.register(r'lessons', LessonViewSet, basename='section-lessons')

# Create nested routers for quiz-related endpoints
quizzes_router = routers.NestedDefaultRouter(courses_router, r'quizzes', lookup='quiz')
quizzes_router.register(r'questions', QuestionViewSet, basename='quiz-questions')
quizzes_router.register(r'attempts', QuizAttemptViewSet, basename='quiz-attempts')

# Create nested routers for question-related endpoints
questions_router = routers.NestedDefaultRouter(quizzes_router, r'questions', lookup='question')
questions_router.register(r'choices', ChoiceViewSet, basename='question-choices')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(courses_router.urls)),
    path('api/', include(sections_router.urls)),
    path('api/', include(quizzes_router.urls)),
    path('api/', include(questions_router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
