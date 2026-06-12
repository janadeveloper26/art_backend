from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.courses.models import Category, Banner, Course, Section, Lesson
from apps.payments.models import SubscriptionPlan, PlanFeature

class Command(BaseCommand):
    help = 'Seeds the database with initial mock data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")
        
        # 1. Categories
        categories = ["Aari", "Tailoring", "Embroidery", "Blouse Design", "Design"]
        cat_objs = {}
        for i, name in enumerate(categories):
            cat, _ = Category.objects.get_or_create(name=name, defaults={'order': i})
            cat_objs[name] = cat
            
        self.stdout.write("Categories created.")

        # 2. Banners
        Banner.objects.get_or_create(
            title="Master Aari Embroidery",
            defaults={
                "subtitle": "50+ hours of premium content",
                "badge": "New",
                "color_start": "0xFF6A1B9A",
                "color_end": "0xFFAB47BC",
                "order": 1,
                "is_active": True
            }
        )
        Banner.objects.get_or_create(
            title="Tailoring Masterclass",
            defaults={
                "subtitle": "From beginner to pro",
                "badge": "Popular",
                "color_start": "0xFF4527A0",
                "color_end": "0xFF7E57C2",
                "order": 2,
                "is_active": True
            }
        )
        self.stdout.write("Banners created.")

        # 3. Instructors (Users)
        priya, _ = User.objects.get_or_create(
            email="priya@example.com",
            defaults={"username": "priya", "first_name": "Priya", "last_name": "Sharma", "is_active": True}
        )
        elena, _ = User.objects.get_or_create(
            email="elena@example.com",
            defaults={"username": "elena", "first_name": "Elena", "last_name": "Rose", "is_active": True}
        )
        self.stdout.write("Instructors created.")

        # 4. Courses
        course1, _ = Course.objects.get_or_create(
            title="Aari Embroidery Masterclass",
            defaults={
                "description": "Master the ancient art of Aari embroidery with this comprehensive masterclass. We cover everything from setting up your frame to executing complex bridal designs with precision.",
                "instructor": priya,
                "category": cat_objs["Aari"],
                "price": 999.00,
                "original_price": 1999.00,
                "level": "INTERMEDIATE",
                "rating": 4.8,
                "reviews_count": 1240,
                "students_count": 3720,
                "duration_str": "12H 45M",
                "is_published": True,
                "is_featured": True
            }
        )
        
        course2, _ = Course.objects.get_or_create(
            title="Modern Zardosi Art",
            defaults={
                "description": "Learn the modern techniques of Zardosi.",
                "instructor": elena,
                "category": cat_objs["Design"],
                "price": 799.00,
                "original_price": 1599.00,
                "badge": "Beginner",
                "discount": "-48%",
                "level": "BEGINNER",
                "rating": 4.9,
                "reviews_count": 520,
                "students_count": 1500,
                "duration_str": "8H 30M",
                "is_published": True,
                "is_featured": True
            }
        )
        self.stdout.write("Courses created.")

        # 5. Sections and Lessons
        section1, _ = Section.objects.get_or_create(
            course=course1,
            title="Section 1: Introduction & Basics",
            defaults={"order": 1}
        )
        
        Lesson.objects.get_or_create(
            section=section1,
            title="Welcome to the Masterclass",
            defaults={
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "order": 1,
                "duration_str": "05:00",
                "is_preview": True
            }
        )
        self.stdout.write("Lessons created.")

        # React & Django Mock Courses
        cat_dev, _ = Category.objects.get_or_create(name="Development", defaults={'order': 10})
        cat_backend, _ = Category.objects.get_or_create(name="Backend", defaults={'order': 11})

        john, _ = User.objects.get_or_create(
            email="john@example.com",
            defaults={"username": "john", "first_name": "John", "last_name": "Doe", "is_active": True}
        )
        jane, _ = User.objects.get_or_create(
            email="jane@example.com",
            defaults={"username": "jane", "first_name": "Jane", "last_name": "Smith", "is_active": True}
        )

        course3, _ = Course.objects.get_or_create(
            title="React Complete Guide",
            defaults={
                "description": "Master React from basics to advanced patterns. Build real-world applications.",
                "instructor": john,
                "instructor_role": "Senior Software Engineer",
                "category": cat_dev,
                "price": 49.99,
                "original_price": 49.99,
                "level": "INTERMEDIATE",
                "students_count": 1205,
                "duration_str": "12h 30m",
                "is_published": True,
                "is_featured": True
            }
        )

        section2, _ = Section.objects.get_or_create(
            course=course3,
            title="Module 1: Introduction",
            defaults={"order": 1}
        )
        Lesson.objects.get_or_create(
            section=section2,
            title="What is React?",
            defaults={
                "video_url": "dummy.mp4",
                "duration_str": "10:05",
                "order": 1,
                "is_preview": True
            }
        )
        Lesson.objects.get_or_create(
            section=section2,
            title="Setup Environment",
            defaults={
                "video_url": "dummy.mp4",
                "duration_str": "15:20",
                "order": 2,
                "is_preview": True
            }
        )

        section3, _ = Section.objects.get_or_create(
            course=course3,
            title="Module 2: Hooks",
            defaults={"order": 2}
        )
        Lesson.objects.get_or_create(
            section=section3,
            title="useState and useEffect",
            defaults={
                "video_url": "dummy.mp4",
                "duration_str": "20:00",
                "order": 1,
                "is_preview": False
            }
        )

        course4, _ = Course.objects.get_or_create(
            title="Advanced Django Architecture",
            defaults={
                "description": "Learn how to build scalable Django applications.",
                "instructor": jane,
                "instructor_role": "Lead Backend Developer",
                "category": cat_backend,
                "price": 69.99,
                "original_price": 69.99,
                "level": "ADVANCED",
                "students_count": 0,
                "duration_str": "8h 15m",
                "is_published": False,
                "is_featured": False
            }
        )
        
        self.stdout.write("Mock React and Django courses created.")

        # 6. Subscription Plans
        plan1, _ = SubscriptionPlan.objects.get_or_create(
            id="monthly",
            defaults={
                "label": "Monthly",
                "price": 299.00,
                "original_price": 499.00,
                "period": "/month",
                "icon": "zap",
                "color_start": "0xFF4527A0",
                "color_end": "0xFF7E57C2",
                "order": 1,
                "is_active": True
            }
        )
        if plan1.features.count() == 0:
            for i, text in enumerate(["Access to all courses", "HD video quality", "Download for offline", "Chat support"]):
                PlanFeature.objects.create(plan=plan1, text=text, order=i)

        plan2, _ = SubscriptionPlan.objects.get_or_create(
            id="yearly",
            defaults={
                "label": "Yearly",
                "price": 1999.00,
                "original_price": 3588.00,
                "period": "/year",
                "icon": "crown",
                "popular": True,
                "savings": "Save ₹1,589",
                "color_start": "0xFF6A1B9A",
                "color_end": "0xFFAB47BC",
                "order": 2,
                "is_active": True
            }
        )
        if plan2.features.count() == 0:
            for i, text in enumerate(["Everything in Monthly", "Priority support", "Certificate of completion", "Exclusive live sessions", "Early access to new courses"]):
                PlanFeature.objects.create(plan=plan2, text=text, order=i)

        plan3, _ = SubscriptionPlan.objects.get_or_create(
            id="lifetime",
            defaults={
                "label": "Lifetime",
                "price": 4999.00,
                "original_price": 12000.00,
                "period": " one-time",
                "icon": "infinity",
                "savings": "Best Value",
                "color_start": "0xFF880E4F",
                "color_end": "0xFFAD1457",
                "order": 3,
                "is_active": True
            }
        )
        if plan3.features.count() == 0:
            for i, text in enumerate(["Everything in Yearly", "Lifetime access", "All future courses", "1-on-1 mentorship sessions", "Physical kit delivery"]):
                PlanFeature.objects.create(plan=plan3, text=text, order=i)

        self.stdout.write("Subscription plans created.")
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
