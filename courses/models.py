from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Q

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def get_progress(self, student):
        """Calculate the overall course progress for a student."""
        enrollment = self.enrollments.filter(student=student).first()
        if not enrollment:
            return 0
        
        total_lessons = Lesson.objects.filter(section__course=self).count()
        if total_lessons == 0:
            return 0
        
        completed_lessons = LessonProgress.objects.filter(
            student=student,
            lesson__section__course=self,
            completed=True
        ).count()
        
        return int((completed_lessons / total_lessons) * 100)

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_progress(self, student):
        """Calculate the section progress for a student."""
        total_lessons = self.lessons.count()
        if total_lessons == 0:
            return 0
        
        completed_lessons = LessonProgress.objects.filter(
            student=student,
            lesson__section=self,
            completed=True
        ).count()
        
        return int((completed_lessons / total_lessons) * 100)

class Lesson(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text='Markdown content for the lesson')
    video_url = models.URLField(max_length=200, null=True, blank=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration = models.PositiveIntegerField(help_text='Duration in minutes', null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.section.course.title} - {self.section.title} - {self.title}"
    
    def get_status(self, student):
        """Get the lesson status for a student."""
        progress = self.student_progress.filter(student=student).first()
        if not progress:
            return 'not_started'
        return 'completed' if progress.completed else 'in_progress'

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    progress = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"
    
    def update_progress(self):
        """Update the enrollment progress based on completed lessons."""
        self.progress = self.course.get_progress(self.student)
        if self.progress == 100:
            self.completed = True
        self.save()

class SectionProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='section_progress')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='student_progress')
    completed = models.BooleanField(default=False)
    progress = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'section']
    
    def __str__(self):
        return f"{self.student.username} - {self.section.title} - {self.progress}% complete"
    
    def update_progress(self):
        """Update the section progress based on completed lessons."""
        self.progress = self.section.get_progress(self.student)
        if self.progress == 100:
            self.completed = True
        self.save()

class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'lesson']
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} - {'Completed' if self.completed else 'In Progress'}"
    
    def save(self, *args, **kwargs):
        """Override save to update section and course progress."""
        super().save(*args, **kwargs)
        
        # Update section progress
        section_progress, _ = SectionProgress.objects.get_or_create(
            student=self.student,
            section=self.lesson.section
        )
        section_progress.update_progress()
        
        # Update enrollment progress
        enrollment = Enrollment.objects.get(
            student=self.student,
            course=self.lesson.section.course
        )
        enrollment.update_progress()

class Bookmark(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'lesson']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"
