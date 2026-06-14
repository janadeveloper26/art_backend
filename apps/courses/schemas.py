from typing import List, Optional
from ninja import Schema
from uuid import UUID


# ---------------------------------------------------------------------------
# Shared / Primitive schemas
# ---------------------------------------------------------------------------

class BannerSchema(Schema):
    title: str
    subtitle: str
    badge: str
    image: str
    colors: List[int]


class InstructorSchema(Schema):
    name: str
    initial: str
    colors: List[int]


class ReviewSchema(Schema):
    id: str
    name: str
    avatar: str          # single initial character
    rating: float
    comment: str
    date: str


# ---------------------------------------------------------------------------
# Course summary (used in home, explore, my-courses)
# ---------------------------------------------------------------------------

class CourseCardSchema(Schema):
    id: str              # UUID as string for Flutter
    title: str
    instructor: str
    category: str
    image: str
    progress: Optional[float] = None
    badge: Optional[str] = None
    discount: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    price: Optional[int] = None
    original_price: Optional[int] = None
    level: Optional[str] = None


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

class HomeDataSchema(Schema):
    categories: List[str]
    banners: List[BannerSchema]
    continue_learning: List[CourseCardSchema]
    featured_courses: List[CourseCardSchema]
    instructors: List[InstructorSchema]


# ---------------------------------------------------------------------------
# Explore
# ---------------------------------------------------------------------------

class ExploreResponseSchema(Schema):
    courses: List[CourseCardSchema]
    categories: List[str]
    filters: List[str]


# ---------------------------------------------------------------------------
# My Courses
# ---------------------------------------------------------------------------

class MyCoursesResponseSchema(Schema):
    ongoing: List[CourseCardSchema]
    completed: List[CourseCardSchema]
    total_enrolled: int
    total_certificates: int


# ---------------------------------------------------------------------------
# Course Detail
# ---------------------------------------------------------------------------

class LessonSchema(Schema):
    id: str
    title: str
    duration: str
    video_url: str
    is_preview: bool
    is_completed: bool


class SectionSchema(Schema):
    id: str
    title: str
    lessons: List[LessonSchema]


class CourseDetailSchema(Schema):
    id: str
    title: str
    description: str
    instructor: str
    instructor_avatar: str
    instructor_role: str
    level: str
    category: str
    duration: str
    lesson_count: int
    rating: float
    reviews: int
    students: int
    price: int
    original_price: int
    image: str
    is_wishlisted: bool
    curriculum: List[SectionSchema]
    reviews_list: List[ReviewSchema]


# ---------------------------------------------------------------------------
# Admin / upload schemas (unchanged)
# ---------------------------------------------------------------------------

class PresignedURLOut(Schema):
    upload_url: str
    s3_key: str


class LessonCreateIn(Schema):
    section_id: UUID
    title: str
    s3_key: str
    file_size: Optional[int] = None
    duration_str: str = '00:00'
    order: int = 0
    is_preview: bool = False


class LessonOut(Schema):
    id: str
    title: str
    duration: str
    video_url: str
    s3_key: Optional[str] = None
    is_preview: bool
    is_completed: bool
    upload_status: str


class CourseCreateIn(Schema):
    title: str
    description: str = ''
    category_id: str | None = None
    price: str = '0.00'
    original_price: str | None = None
    level: str = 'BEGINNER'
    instructor_role: str = 'Instructor'
    is_published: bool = False
    is_featured: bool = False
