from typing import List, Optional
from ninja import Schema
from uuid import UUID

class BannerSchema(Schema):
    title: str
    subtitle: str
    badge: str
    image: str
    colors: List[int]

class CourseCardSchema(Schema):
    id: UUID
    title: str
    instructor: str
    category: str
    image: str
    progress: Optional[float] = None
    rating: float
    reviews: int
    price: float
    original_price: float
    badge: Optional[str] = None
    discount: Optional[str] = None

class HomeDataSchema(Schema):
    categories: List[str]
    banners: List[BannerSchema]
    continue_learning: List[CourseCardSchema]
    featured_courses: List[CourseCardSchema]

class LessonSchema(Schema):
    id: UUID
    title: str
    duration: str
    video_url: str
    is_preview: bool
    is_completed: bool

class SectionSchema(Schema):
    id: UUID
    title: str
    lessons: List[LessonSchema]

class CourseDetailSchema(Schema):
    id: UUID
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
    price: float
    original_price: float
    image: str
    is_wishlisted: bool
    curriculum: List[SectionSchema]
