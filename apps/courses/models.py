import uuid
from django.db import models
from accounts.models import User

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'categories'
        ordering = ['order']

    def __str__(self):
        return self.name

class Banner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    badge = models.CharField(max_length=50)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    color_start = models.CharField(max_length=20, default="0xFF6A1B9A")
    color_end = models.CharField(max_length=20, default="0xFFAB47BC")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'banners'
        ordering = ['order']

class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='teaching_courses')
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    badge = models.CharField(max_length=50, null=True, blank=True)
    discount = models.CharField(max_length=50, null=True, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    
    # Pre-computed stats
    rating = models.FloatField(default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)
    students_count = models.PositiveIntegerField(default=0)
    duration_str = models.CharField(max_length=50, default="0H 0M")
    
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'

class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = 'sections'
        ordering = ['order']

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons', null=True, blank=True)
    title = models.CharField(max_length=255)
    video_url = models.URLField(max_length=500)
    order = models.PositiveIntegerField()
    duration_str = models.CharField(max_length=50, default="00:00")
    is_preview = models.BooleanField(default=False)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_progress'
        unique_together = ('user', 'lesson')

