from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import Course, Section, Lesson
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Creates sample courses with sections and lessons'

    def handle(self, *args, **options):
        # Create or get instructor
        instructor, _ = User.objects.get_or_create(
            username='instructor',
            email='instructor@dataidea.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'is_active': True
            }
        )
        instructor.set_password('instructor123')
        instructor.save()

        # Set user type as instructor
        profile = instructor.userprofile
        profile.user_type = 'instructor'
        profile.save()

        # Sample courses data
        courses_data = [
            {
                'title': 'Python Programming Fundamentals',
                'description': 'Master the basics of Python programming language. Learn syntax, data types, control structures, functions, and object-oriented programming concepts.',
                'sections': [
                    {
                        'title': 'Getting Started with Python',
                        'lessons': [
                            {
                                'title': 'Introduction to Python',
                                'content': '# Introduction to Python\n\nPython is a high-level, interpreted programming language known for its simplicity and readability.\n\n## Why Python?\n\n- Easy to learn and read\n- Large standard library\n- Extensive third-party packages\n- Cross-platform compatibility\n- Strong community support',
                                'duration': 30
                            },
                            {
                                'title': 'Setting Up Your Development Environment',
                                'content': '# Setting Up Python\n\n## Installing Python\n\n1. Download Python from python.org\n2. Install VS Code or PyCharm\n3. Set up virtual environments\n\n## Your First Python Program\n\n```python\nprint("Hello, World!")\n```',
                                'duration': 45
                            }
                        ]
                    },
                    {
                        'title': 'Python Basics',
                        'lessons': [
                            {
                                'title': 'Variables and Data Types',
                                'content': '# Variables and Data Types\n\n## Basic Data Types\n\n```python\n# Numbers\nx = 42  # integer\ny = 3.14  # float\n\n# Strings\nname = "Python"\n\n# Booleans\nis_active = True\n```',
                                'duration': 60
                            }
                        ]
                    }
                ]
            },
            {
                'title': 'Data Analysis with Python',
                'description': 'Learn how to analyze data using Python. Cover pandas, numpy, matplotlib, and data visualization techniques.',
                'sections': [
                    {
                        'title': 'Introduction to Data Analysis',
                        'lessons': [
                            {
                                'title': 'Understanding Data Analysis',
                                'content': '# Data Analysis Fundamentals\n\nData analysis is the process of inspecting, cleaning, transforming, and modeling data to discover useful information.\n\n## Key Libraries\n\n- Pandas\n- NumPy\n- Matplotlib',
                                'duration': 45
                            }
                        ]
                    },
                    {
                        'title': 'Working with Pandas',
                        'lessons': [
                            {
                                'title': 'Pandas DataFrame Basics',
                                'content': '# Pandas DataFrame\n\n```python\nimport pandas as pd\n\n# Create a DataFrame\ndf = pd.DataFrame({\n    "Name": ["John", "Anna"],\n    "Age": [28, 22]\n})\n```',
                                'duration': 60
                            }
                        ]
                    }
                ]
            },
            {
                'title': 'Machine Learning with Python',
                'description': 'Explore machine learning concepts and implementations using Python. Learn about supervised and unsupervised learning, model evaluation, and practical applications.',
                'sections': [
                    {
                        'title': 'Machine Learning Basics',
                        'lessons': [
                            {
                                'title': 'Introduction to Machine Learning',
                                'content': '# Machine Learning Fundamentals\n\nMachine learning is a subset of artificial intelligence that focuses on building systems that learn from data.\n\n## Types of Machine Learning\n\n1. Supervised Learning\n2. Unsupervised Learning\n3. Reinforcement Learning',
                                'duration': 45
                            }
                        ]
                    },
                    {
                        'title': 'Supervised Learning',
                        'lessons': [
                            {
                                'title': 'Linear Regression',
                                'content': '# Linear Regression\n\n```python\nfrom sklearn.linear_model import LinearRegression\n\n# Create and train model\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n```',
                                'duration': 60
                            }
                        ]
                    }
                ]
            }
        ]

        # Create courses
        for course_data in courses_data:
            course = Course.objects.create(
                title=course_data['title'],
                description=course_data['description'],
                instructor=instructor,
                is_published=True
            )
            
            for section_idx, section_data in enumerate(course_data['sections'], 1):
                section = Section.objects.create(
                    course=course,
                    title=section_data['title'],
                    order=section_idx
                )
                
                for lesson_idx, lesson_data in enumerate(section_data['lessons'], 1):
                    Lesson.objects.create(
                        section=section,
                        title=lesson_data['title'],
                        content=lesson_data['content'],
                        order=lesson_idx,
                        duration=lesson_data['duration']
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created course: {course.title}')
            ) 