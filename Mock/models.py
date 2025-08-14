from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Ustoz'),
        ('student', 'Talaba'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Foydalanuvchi roli")
    is_approved = models.BooleanField(default=True, verbose_name="Tasdiqlangan")
    
    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

class Question(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='questions', verbose_name="Savol muallifi")
    text = models.TextField(verbose_name="Savol matni")
    image = models.ImageField(upload_to='question_images/', blank=True, null=True, verbose_name="Savol rasmi")
    QUESTION_TYPES = (
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='reading', verbose_name="Savol turi")

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255, verbose_name="Variant matni")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri javob")

    def __str__(self):
        return self.text

class Exam(models.Model):
    title = models.CharField(max_length=255, verbose_name="Imtihon nomi")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_exams',
        verbose_name="Ustoz"
    )
    questions = models.ManyToManyField(Question, related_name='exams', verbose_name="Savollar")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="Imtihon vaqti (daqiqa)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Imtihon"
        verbose_name_plural = "Imtihonlar"

from django.db import models
from django.conf import settings

class UserAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, verbose_name="Imtihon")
    score = models.IntegerField(default=0, verbose_name="Ball")
    correct_answers = models.IntegerField(default=0, verbose_name="To'g'ri javoblar soni")
    incorrect_answers = models.IntegerField(default=0, verbose_name="Noto'g'ri javoblar soni")  # Yangi maydon
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Boshlangan vaqti")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tugatilgan vaqti")
    is_completed = models.BooleanField(default=False, verbose_name="Tugatilgan")

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} ({self.score})"

    @property
    def percentage(self):
        """Foizdagi natija"""
        total_questions = self.exam.questions.count()
        if total_questions > 0:
            return (self.correct_answers / total_questions) * 100
        return 0

    class Meta:
        verbose_name = "Foydalanuvchi ishlagan test"
        verbose_name_plural = "Foydalanuvchi ishlagan testlar"

class UserAnswer(models.Model):
    attempt = models.ForeignKey(UserAttempt, on_delete=models.CASCADE, related_name='useranswers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.text[:20]}"
