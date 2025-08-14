from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomUser, Question, AnswerOption, Exam, UserAttempt, UserAnswer


# CustomUser modeli uchun Admin paneli sozlamalari
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_approved', 'is_staff', 'is_active')
    list_filter = ('role', 'is_approved', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_per_page = 25  # Har sahifada 25 ta yozuv
    actions = ['approve_teachers', 'deactivate_users']

    # Ustozlarni tasdiqlash funksiyasi
    def approve_teachers(self, request, queryset):
        unapproved_teachers = queryset.filter(role='teacher', is_approved=False)
        updated = unapproved_teachers.update(is_approved=True)
        self.message_user(request, f"{updated} ta ustoz akkaunti muvaffaqiyatli tasdiqlandi.")
    approve_teachers.short_description = "Tanlangan ustozlarni tasdiqlash"

    # Foydalanuvchilarni deaktivatsiya qilish
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ta foydalanuvchi deaktivatsiya qilindi.")
    deactivate_users.short_description = "Tanlangan foydalanuvchilarni deaktivatsiya qilish"

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Shaxsiy ma\'lumotlar', {'fields': ('first_name', 'last_name', 'email')}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Qo\'shimcha ma\'lumotlar', {'fields': ('role', 'is_approved')}),
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_approved', 'is_staff', 'is_active'),
        }),
    )


# Savollar va variantlarni bir joyda boshqarish uchun
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 4
    fields = ('text', 'is_correct')
    show_change_link = True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question_type', 'author', 'view_exams')
    list_filter = ('question_type', 'author')
    search_fields = ('text', 'author__username')
    inlines = [AnswerOptionInline]
    list_per_page = 25
    list_select_related = ('author',)

    def text_preview(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_preview.short_description = "Savol matni"

    def view_exams(self, obj):
        exams = obj.exams.all()  # related_name='exams' ishlatiladi
        if not exams:
            return "Hech qaysi imtihonda ishlatilmagan"
        links = []
        for exam in exams:
            url = reverse('admin:Mock_exam_change', args=[exam.pk])
            links.append(f'<a href="{url}">{exam.title}</a>')
        return format_html(", ".join(links))
    view_exams.short_description = "Qaysi imtihonlarda ishlatilgan"
    view_exams.allow_tags = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'duration_minutes', 'created_at', 'question_count')
    list_filter = ('teacher', 'created_at')
    search_fields = ('title', 'teacher__username')
    filter_horizontal = ('questions',)
    list_per_page = 25
    list_select_related = ('teacher',)

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Savollar soni"


@admin.register(UserAttempt)
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'score', 'correct_answers', 'incorrect_answers', 'percentage', 'completed_at')
    list_filter = ('exam', 'user', 'completed_at')
    search_fields = ('user__username', 'exam__title')
    readonly_fields = ('user', 'exam', 'score', 'correct_answers', 'incorrect_answers', 'started_at', 'completed_at')
    list_per_page = 25
    list_select_related = ('user', 'exam')

    def percentage(self, obj):
        return f"{obj.percentage:.0f}%"
    percentage.short_description = "Foiz"


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct')
    list_filter = ('attempt__exam', 'question__question_type')
    search_fields = ('attempt__user__username', 'question__text')
    readonly_fields = ('attempt', 'question', 'selected_option')
    list_per_page = 25
    list_select_related = ('attempt__user', 'attempt__exam', 'question', 'selected_option')

    def is_correct(self, obj):
        return obj.selected_option.is_correct if obj.selected_option else False
    is_correct.short_description = "To'g'ri javob"
    is_correct.boolean = True