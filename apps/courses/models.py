import uuid
from django.db import models
from apps.accounts.models import User


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

    def __str__(self):
        return self.title


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='courses'
    )
    instructor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='teaching_courses'
    )
    # Instructor display overrides (shown on course detail screen)
    instructor_role = models.CharField(
        max_length=255,
        default='Instructor',
        help_text='e.g. "Expert Instructor · 5 years exp"',
    )
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    badge = models.CharField(max_length=50, null=True, blank=True)
    discount = models.CharField(max_length=50, null=True, blank=True)
    level = models.CharField(
        max_length=20, choices=Level.choices, default=Level.BEGINNER
    )

    # Pre-computed stats (updated via signals or management command)
    rating = models.FloatField(default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)
    students_count = models.PositiveIntegerField(default=0)
    duration_str = models.CharField(max_length=50, default='0H 0M')

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'

    def __str__(self):
        return self.title

    def get_instructor_name(self) -> str:
        if self.instructor:
            return self.instructor.get_full_name() or self.instructor.username
        return 'Unknown'

    def get_thumbnail_url(self) -> str:
        if self.thumbnail:
            return self.thumbnail.url
        return ''


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='sections'
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = 'sections'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name='lessons', null=True, blank=True
    )
    title = models.CharField(max_length=255)
    video_url = models.URLField(max_length=500)
    s3_key = models.CharField(max_length=500, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField()
    duration_str = models.CharField(max_length=50, default='00:00')
    is_preview = models.BooleanField(default=False)
    upload_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('ready', 'Ready'), ('error', 'Error')],
        default='ready',
    )

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

    def __str__(self):
        return self.title


class UserProgress(models.Model):
    """Tracks per-lesson completion for a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_progress'
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user} — {self.lesson}'


class Enrollment(models.Model):
    """Tracks which courses a user is enrolled in."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='enrollments'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    # Set when all lessons are completed
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.user} → {self.course}'

    def compute_progress(self) -> float:
        """Return completion ratio 0.0–1.0 based on UserProgress records."""
        lesson_ids = list(
            Lesson.objects.filter(section__course=self.course).values_list('id', flat=True)
        )
        total = len(lesson_ids)
        if total == 0:
            return 0.0
        completed = UserProgress.objects.filter(
            user=self.user, lesson_id__in=lesson_ids, completed=True
        ).count()
        return round(completed / total, 4)


class Review(models.Model):
    """Course review submitted by an enrolled user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.FloatField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_reviews'
        unique_together = ('course', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.course} ({self.rating}★)'

    def get_reviewer_name(self) -> str:
        return self.user.get_full_name() or self.user.username

    def get_reviewer_initial(self) -> str:
        name = self.get_reviewer_name()
        return name[0].upper() if name else '?'

    def get_date_display(self) -> str:
        from django.utils import timezone
        from datetime import timedelta

        delta = timezone.now() - self.created_at
        if delta < timedelta(minutes=1):
            return 'Just now'
        if delta < timedelta(hours=1):
            mins = int(delta.seconds / 60)
            return f'{mins} minute{"s" if mins > 1 else ""} ago'
        if delta < timedelta(days=1):
            hrs = int(delta.seconds / 3600)
            return f'{hrs} hour{"s" if hrs > 1 else ""} ago'
        if delta.days < 7:
            return f'{delta.days} day{"s" if delta.days > 1 else ""} ago'
        if delta.days < 30:
            weeks = delta.days // 7
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        months = delta.days // 30
        return f'{months} month{"s" if months > 1 else ""} ago'
