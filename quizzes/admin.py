from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 6

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'quiz', 'question_type', 'order', 'points')
    list_filter = ('quiz', 'question_type')
    search_fields = ('text', 'quiz__title')
    ordering = ('quiz', 'order')

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'course', 'lesson', 'passing_score', 'created_at')
    list_filter = ('course', 'passing_score')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'text_answer', 'is_correct')
    can_delete = False

class QuizAttemptAdmin(admin.ModelAdmin):
    inlines = [StudentAnswerInline]
    list_display = ('student', 'quiz', 'score', 'passed', 'started_at', 'completed_at')
    list_filter = ('passed', 'started_at', 'completed_at')
    search_fields = ('student__username', 'quiz__title')
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    readonly_fields = ('score', 'passed', 'started_at', 'completed_at')

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
