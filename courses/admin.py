from django.contrib import admin
from .models import Course, Section, Lesson, Enrollment, LessonProgress

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

class SectionAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')

class SectionInline(admin.StackedInline):
    model = Section
    extra = 1
    show_change_link = True

class CourseAdmin(admin.ModelAdmin):
    inlines = [SectionInline]
    list_display = ('title', 'instructor', 'created_at', 'is_published')
    list_filter = ('is_published', 'instructor')
    search_fields = ('title', 'description', 'instructor__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed')
    list_filter = ('completed', 'enrolled_at')
    search_fields = ('student__username', 'course__title')
    ordering = ('-enrolled_at',)
    date_hierarchy = 'enrolled_at'

class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'completed', 'last_accessed')
    list_filter = ('completed', 'last_accessed')
    search_fields = ('student__username', 'lesson__title')
    ordering = ('-last_accessed',)
    date_hierarchy = 'last_accessed'

admin.site.register(Course, CourseAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Lesson)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(LessonProgress, LessonProgressAdmin)
