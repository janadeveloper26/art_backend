from django.contrib import admin
from .models import Category, Banner, Course, Section, Lesson, UserProgress

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'is_active', 'order')
    list_filter = ('is_active',)

class SectionInline(admin.TabularInline):
    model = Section
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'is_published', 'is_featured', 'created_at')
    list_filter = ('is_published', 'is_featured', 'category')
    inlines = [SectionInline]

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'is_preview')
    list_filter = ('section__course', 'is_preview')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'last_watched_at')
    list_filter = ('completed',)
