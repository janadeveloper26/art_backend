import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.courses.models import Category, Banner, Course, Section, Lesson, Review, Enrollment
from apps.payments.models import SubscriptionPlan, PlanFeature
from apps.supply.models import SupplyCategory, Product


class Command(BaseCommand):
    help = 'Seeds the database with initial mock data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        now = timezone.now()

        # ------------------------------------------------------------------ #
        # 0. Demo users
        # ------------------------------------------------------------------ #
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@art.com',
                'is_staff': True,
                'is_superuser': True,
                'is_approved': True,
            },
        )
        if admin:
            admin.set_password('admin123')
            admin.save(update_fields=['password'])

        priya, _ = User.objects.get_or_create(
            username='priya_sharma',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'email': 'priya@example.com',
                'is_active': True,
                'is_approved': True,
            },
        )

        elena, _ = User.objects.get_or_create(
            username='elena_rose',
            defaults={
                'first_name': 'Elena',
                'last_name': 'Rose',
                'email': 'elena@example.com',
                'is_active': True,
                'is_approved': True,
            },
        )

        student, _ = User.objects.get_or_create(
            username='student',
            defaults={
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'student@art.com',
                'is_active': True,
                'is_approved': True,
            },
        )
        if student:
            student.set_password('student123')
            student.save(update_fields=['password'])

        self.stdout.write("Users created (admin/admin123, student/student123).")

        # ------------------------------------------------------------------ #
        # 1. Course Categories
        # ------------------------------------------------------------------ #
        categories = ['Aari', 'Tailoring', 'Embroidery', 'Blouse Design', 'Design']
        cat_objs = {}
        for i, name in enumerate(categories):
            cat, _ = Category.objects.get_or_create(name=name, defaults={'order': i})
            cat_objs[name] = cat
        self.stdout.write("Course categories created.")

        # ------------------------------------------------------------------ #
        # 2. Banners
        # ------------------------------------------------------------------ #
        Banner.objects.get_or_create(
            title='Master Aari Embroidery',
            defaults={
                'subtitle': '50+ hours of premium content',
                'badge': 'New',
                'color_start': '0xFF6A1B9A',
                'color_end': '0xFFAB47BC',
                'order': 1,
                'is_active': True,
            },
        )
        Banner.objects.get_or_create(
            title='Tailoring Masterclass',
            defaults={
                'subtitle': 'From beginner to pro',
                'badge': 'Popular',
                'color_start': '0xFF4527A0',
                'color_end': '0xFF7E57C2',
                'order': 2,
                'is_active': True,
            },
        )
        self.stdout.write('Banners created.')

        # ------------------------------------------------------------------ #
        # 3. Courses, Sections, Lessons
        # ------------------------------------------------------------------ #
        course1, _ = Course.objects.get_or_create(
            title='Aari Embroidery Masterclass',
            defaults={
                'description': 'Master the ancient art of Aari embroidery with this comprehensive masterclass. We cover everything from setting up your frame to executing complex bridal designs with precision.',
                'instructor': priya,
                'category': cat_objs['Aari'],
                'instructor_role': 'Expert Instructor \u00b7 5 years exp',
                'price': Decimal('999.00'),
                'original_price': Decimal('1999.00'),
                'level': Course.Level.INTERMEDIATE,
                'rating': 4.8,
                'reviews_count': 1240,
                'students_count': 3720,
                'duration_str': '12H 45M',
                'is_published': True,
                'is_featured': True,
            },
        )

        course2, _ = Course.objects.get_or_create(
            title='Modern Zardosi Art',
            defaults={
                'description': 'Learn the modern techniques of Zardosi. Perfect for beginners who want to explore this beautiful embroidery style.',
                'instructor': elena,
                'category': cat_objs['Design'],
                'instructor_role': 'Master Artisan \u00b7 10 years exp',
                'price': Decimal('799.00'),
                'original_price': Decimal('1599.00'),
                'badge': 'Beginner',
                'discount': '-48%',
                'level': Course.Level.BEGINNER,
                'rating': 4.9,
                'reviews_count': 520,
                'students_count': 1500,
                'duration_str': '8H 30M',
                'is_published': True,
                'is_featured': True,
            },
        )
        self.stdout.write('Courses created.')

        # Sections & Lessons for course1
        sec1, _ = Section.objects.get_or_create(
            course=course1,
            title='Introduction & Basics',
            defaults={'order': 1},
        )
        Lesson.objects.get_or_create(
            section=sec1,
            title='Welcome to the Masterclass',
            defaults={
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'order': 1,
                'duration_str': '05:00',
                'is_preview': True,
            },
        )
        Lesson.objects.get_or_create(
            section=sec1,
            title='Tools & Materials Needed',
            defaults={
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
                'order': 2,
                'duration_str': '08:30',
                'is_preview': True,
            },
        )

        sec2, _ = Section.objects.get_or_create(
            course=course1,
            title='Basic Stitches',
            defaults={'order': 2},
        )
        Lesson.objects.get_or_create(
            section=sec2,
            title='The Chain Stitch',
            defaults={
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
                'order': 1,
                'duration_str': '12:00',
                'is_preview': False,
            },
        )

        # Sections & Lessons for course2
        sec3, _ = Section.objects.get_or_create(
            course=course2,
            title='Getting Started',
            defaults={'order': 1},
        )
        Lesson.objects.get_or_create(
            section=sec3,
            title='Introduction to Zardosi',
            defaults={
                'video_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
                'order': 1,
                'duration_str': '06:00',
                'is_preview': True,
            },
        )
        self.stdout.write('Sections & Lessons created.')

        # ------------------------------------------------------------------ #
        # 4. Enrollments & Progress (student enrolled in course1)
        # ------------------------------------------------------------------ #
        enrollment, created = Enrollment.objects.get_or_create(
            user=student,
            course=course1,
        )
        if created:
            self.stdout.write(f'  Enrolled student in {course1.title}')

        # Mark first lesson as completed
        first_lesson = Lesson.objects.filter(section__course=course1).order_by('order').first()
        if first_lesson:
            from apps.courses.models import UserProgress
            UserProgress.objects.get_or_create(
                user=student,
                lesson=first_lesson,
                defaults={'completed': True, 'last_watched_at': now},
            )

        # ------------------------------------------------------------------ #
        # 5. Reviews
        # ------------------------------------------------------------------ #
        Review.objects.get_or_create(
            course=course1,
            user=student,
            defaults={
                'rating': 5.0,
                'comment': 'Amazing course! Learned so much in just a few days.',
            },
        )

        # ------------------------------------------------------------------ #
        # 6. Subscription Plans
        # ------------------------------------------------------------------ #
        plan1, _ = SubscriptionPlan.objects.get_or_create(
            id='monthly',
            defaults={
                'label': 'Monthly',
                'price': Decimal('299.00'),
                'original_price': Decimal('499.00'),
                'period': '/month',
                'icon': 'zap',
                'color_start': '0xFF4527A0',
                'color_end': '0xFF7E57C2',
                'order': 1,
                'is_active': True,
            },
        )
        if plan1.features.count() == 0:
            for i, text in enumerate([
                'Access to all courses', 'HD video quality',
                'Download for offline', 'Chat support',
            ]):
                PlanFeature.objects.create(plan=plan1, text=text, order=i)

        plan2, _ = SubscriptionPlan.objects.get_or_create(
            id='yearly',
            defaults={
                'label': 'Yearly',
                'price': Decimal('1999.00'),
                'original_price': Decimal('3588.00'),
                'period': '/year',
                'icon': 'crown',
                'popular': True,
                'savings': 'Save \u20b91,589',
                'color_start': '0xFF6A1B9A',
                'color_end': '0xFFAB47BC',
                'order': 2,
                'is_active': True,
            },
        )
        if plan2.features.count() == 0:
            for i, text in enumerate([
                'Everything in Monthly', 'Priority support',
                'Certificate of completion', 'Exclusive live sessions',
                'Early access to new courses',
            ]):
                PlanFeature.objects.create(plan=plan2, text=text, order=i)

        plan3, _ = SubscriptionPlan.objects.get_or_create(
            id='lifetime',
            defaults={
                'label': 'Lifetime',
                'price': Decimal('4999.00'),
                'original_price': Decimal('12000.00'),
                'period': '\xa0one-time',
                'icon': 'infinity',
                'savings': 'Best Value',
                'color_start': '0xFF880E4F',
                'color_end': '0xFFAD1457',
                'order': 3,
                'is_active': True,
            },
        )
        if plan3.features.count() == 0:
            for i, text in enumerate([
                'Everything in Yearly', 'Lifetime access',
                'All future courses', '1-on-1 mentorship sessions',
                'Physical kit delivery',
            ]):
                PlanFeature.objects.create(plan=plan3, text=text, order=i)
        self.stdout.write('Subscription plans created.')

        # ------------------------------------------------------------------ #
        # 7. Supply Categories & Products
        # ------------------------------------------------------------------ #
        supply_cats = {
            'Threads': 0,
            'Fabrics': 1,
            'Tools': 2,
            'Beads & Stones': 3,
            'Kits': 4,
        }
        supply_cat_objs = {}
        for name, order in supply_cats.items():
            c, _ = SupplyCategory.objects.get_or_create(name=name, defaults={'order': order})
            supply_cat_objs[name] = c

        products_data = [
            {
                'name': 'Aari Embroidery Thread Pack (24 Colors)',
                'description': 'High-quality cotton threads for Aari work. 24 vibrant colors included.',
                'price': Decimal('349.00'),
                'original_price': Decimal('499.00'),
                'image_url': 'https://picsum.photos/seed/threads1/400/400',
                'category': supply_cat_objs['Threads'],
                'rating': 4.7,
                'reviews_count': 230,
                'in_stock': True,
            },
            {
                'name': 'Gold-Plated Aari Needle Set (6 Pcs)',
                'description': 'Premium gold-plated needles for smooth Aari embroidery.',
                'price': Decimal('199.00'),
                'original_price': Decimal('299.00'),
                'image_url': 'https://picsum.photos/seed/needles1/400/400',
                'category': supply_cat_objs['Tools'],
                'rating': 4.5,
                'reviews_count': 180,
                'in_stock': True,
            },
            {
                'name': 'Pure Silk Fabric - White (1 Meter)',
                'description': 'Luxurious pure silk fabric perfect for bridal embroidery projects.',
                'price': Decimal('599.00'),
                'original_price': Decimal('799.00'),
                'image_url': 'https://picsum.photos/seed/fabric1/400/400',
                'category': supply_cat_objs['Fabrics'],
                'rating': 4.8,
                'reviews_count': 95,
                'in_stock': True,
            },
            {
                'name': 'Glass Beads Mix Pack (500g)',
                'description': 'Mixed color glass beads for embellishment and zardosi work.',
                'price': Decimal('249.00'),
                'original_price': Decimal('349.00'),
                'image_url': 'https://picsum.photos/seed/beads1/400/400',
                'category': supply_cat_objs['Beads & Stones'],
                'rating': 4.6,
                'reviews_count': 145,
                'in_stock': True,
            },
            {
                'name': 'Beginner Aari Kit - Complete Set',
                'description': 'Everything you need to start Aari embroidery: frame, needles, threads, fabric, and guide.',
                'price': Decimal('1299.00'),
                'original_price': Decimal('1999.00'),
                'image_url': 'https://picsum.photos/seed/kit1/400/400',
                'category': supply_cat_objs['Kits'],
                'rating': 4.9,
                'reviews_count': 310,
                'in_stock': True,
            },
            {
                'name': 'Sequins Assorted Pack (100 Pcs)',
                'description': 'Assorted size and color sequins for adding sparkle to designs.',
                'price': Decimal('149.00'),
                'original_price': Decimal('199.00'),
                'image_url': 'https://picsum.photos/seed/sequins1/400/400',
                'category': supply_cat_objs['Beads & Stones'],
                'rating': 4.3,
                'reviews_count': 67,
                'in_stock': True,
            },
        ]
        for pd in products_data:
            Product.objects.get_or_create(
                name=pd['name'],
                defaults=pd,
            )
        self.stdout.write('Supply categories & products created.')

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
