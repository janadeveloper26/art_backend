from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Banner, Course, Section, Lesson, UserProgress, Enrollment, Review, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'is_active', 'order')
    list_filter = ('is_active',)
    ordering = ('order',)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'instructor', 'level',
        'price', 'rating', 'students_count', 'is_published', 'is_featured', 'created_at',
    )
    list_filter = ('is_published', 'is_featured', 'level', 'category')
    search_fields = ('title', 'instructor__email')
    inlines = [SectionInline]
    readonly_fields = ('rating', 'reviews_count', 'students_count', 'created_at')


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('title', 'video', 'order', 'duration_str', 'is_preview', 'upload_status')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'duration_str', 'is_preview', 'upload_status', 'video_link')
    list_filter = ('section__course', 'is_preview', 'upload_status')
    search_fields = ('title',)
    raw_id_fields = ('video',)

    def video_link(self, obj):
        url = obj.cloudfront_url()
        if url:
            return format_html('<a href="{}" target="_blank">Play</a>', url)
        return '-'
    video_link.short_description = 'Video'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'file', 'duration_str', 'uploaded_at', 'video_preview')
    search_fields = ('title',)
    readonly_fields = ('uploaded_at',)

    def video_preview(self, obj):
        url = obj.cloudfront_url()
        if url:
            return format_html(
                '<video width="320" height="180" controls><source src="{}" type="video/mp4"></video>',
                url,
            )
        return '-'
    video_preview.short_description = 'Preview'


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'last_watched_at')
    list_filter = ('completed',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'completed_at')
    list_filter = ('course',)
    search_fields = ('user__email', 'course__title')
    readonly_fields = ('enrolled_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'created_at')
    list_filter = ('course', 'rating')
    search_fields = ('user__email', 'course__title')
    readonly_fields = ('created_at',)
