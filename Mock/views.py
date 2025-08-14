from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse, Http404
from django.db.models import Count
from .models import CustomUser, Question, AnswerOption, Exam, UserAttempt, UserAnswer
from django.db import transaction
from django.utils.timezone import now
from django.utils import timezone
import logging
import json

logger = logging.getLogger(__name__)

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

def is_student(user):
    return user.is_authenticated and user.role == 'student'


# --- Umumiy sahifalar ---
def index(request):
    """ Bosh sahifani ko'rsatadi. """
    return render(request, 'index.html')


@login_required(login_url='signin')
def tests(request):
    """ Talaba uchun mavjud testlar ro'yxatini ko'rsatadi. """
    if not is_student(request.user):
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q.")
        return redirect('index')

    exams = Exam.objects.all().annotate(num_questions=Count('questions')).order_by('-created_at')
    context = {'exams': exams}
    return render(request, 'tests.html', context)

def signup(request):
    """
    Ro'yxatdan o'tish sahifasi va logikasi.
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')
        role = request.POST.get('role', 'student')

        if password != password_confirmation:
            messages.error(request, "Parollar bir-biriga mos kelmadi.")
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi band.")
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Bu elektron pochta manzili band.")
        else:
            # Ustoz roli uchun tasdiqlash logikasi
            if role == 'teacher':
                is_approved = False
                messages.success(request, "Ro'yxatdan o'tish so'rovingiz qabul qilindi. Sizning akkauntingiz admin tomonidan tasdiqlangach, tizimga kirishingiz mumkin.")
            else:
                is_approved = True
                messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz. Endi tizimga kirishingiz mumkin.")

            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_approved=is_approved
            )

            if is_approved:
                login(request, user)
                return redirect('index')
            else:
                return redirect('signin')

    return render(request, 'signup.html')

# signin funksiyasini yangilash
def signin(request):
    # ... (signin funksiyasining boshlanishi)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Foydalanuvchi tasdiqlanganmi, tekshirish
            if user.is_approved:
                login(request, user)
                messages.success(request, f"Xush kelibsiz, {user.username}!")
                return redirect('index')
            else:
                messages.error(request, "Sizning akkauntingiz hali tasdiqlanmagan. Iltimos, sabr qiling.")
        else:
            messages.error(request, "Foydalanuvchi nomi yoki parol noto'g'ri.")
    return render(request, 'signin.html')

def logout_view(request):
    """ Tizimdan chiqish. """
    logout(request)
    messages.success(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('signin')


# --- Parolni tiklash ---
def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            current_site = request.get_host()
            subject = "Parolni tiklash so'rovi"
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://{current_site}/password-reset/confirm/{uidb64}/{token}/"

            message = render_to_string('emails/password_reset_email.html', {
                'user': user, 'reset_link': reset_link
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            messages.success(request, "Parolni tiklash bo'yicha yo'riqnoma elektron pochtangizga yuborildi.")
            return redirect('password_reset_done')
        except User.DoesNotExist:
            messages.error(request, "Ushbu elektron pochta manzili topilmadi.")

    return render(request, 'password_reset_request.html')

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            new_password_confirm = request.POST.get('new_password_confirm')
            if new_password == new_password_confirm:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Parolingiz muvaffaqiyatli yangilandi. Endi tizimga kirishingiz mumkin.")
                return redirect('signin')
            else:
                messages.error(request, "Parollar bir-biriga mos kelmadi.")
        return render(request, 'password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
    else:
        messages.error(request, "Parolni tiklash havolasi yaroqsiz yoki muddati tugagan.")
        return redirect('password_reset_request')


@login_required(login_url='signin')
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Eski yakunlanmagan urinishlarni o'chirish
    UserAttempt.objects.filter(user=request.user, exam=exam, is_completed=False).delete()
    
    # Yangi urinish yaratish
    attempt = UserAttempt.objects.create(
        user=request.user,
        exam=exam,
        started_at=timezone.now(),
        is_completed=False
    )
    
    logger.debug(f"New attempt created: exam_id={exam.id}, attempt_id={attempt.id}, started_at={attempt.started_at}")
    
    # Joriy savol indeksini seansga saqlash
    request.session['current_q_index'] = 0
    
    return redirect('test_page', exam_id=exam.id, attempt_id=attempt.id)

@login_required(login_url='signin')
def test_page(request, exam_id, attempt_id):
    exam = get_object_or_404(Exam, id=exam_id)
    attempt = get_object_or_404(UserAttempt, id=attempt_id, user=request.user, exam=exam)
    if attempt.is_completed:
        return redirect('view_result_detail', attempt_id=attempt.id)
    
    questions = list(exam.questions.all().order_by('id'))
    total_questions = len(questions)
    current_q_index = request.session.get('current_q_index', 0)
    
    nav_index = request.GET.get('question_index')
    if nav_index is not None and nav_index.isdigit():
        current_q_index = int(nav_index)
        if 0 <= current_q_index < total_questions:
            request.session['current_q_index'] = current_q_index
        else:
            current_q_index = request.session.get('current_q_index', 0)

    if request.method == 'POST':
        selected_option_id = request.POST.get('selected_option')
        question_id = request.POST.get('question_id')
        if selected_option_id and question_id:
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question_id=question_id,
                defaults={'selected_option_id': selected_option_id}
            )
        action = request.POST.get('action')
        if action == 'next' and current_q_index < total_questions - 1:
            current_q_index += 1
            request.session['current_q_index'] = current_q_index
            return redirect('test_page', exam_id=exam.id, attempt_id=attempt.id)
        elif action == 'prev' and current_q_index > 0:
            current_q_index -= 1
            request.session['current_q_index'] = current_q_index
            return redirect('test_page', exam_id=exam.id, attempt_id=attempt.id)
        elif action == 'finish':
            with transaction.atomic():
                correct_answers_count = sum(1 for answer in attempt.useranswers.all() if answer.selected_option and answer.selected_option.is_correct)
                attempt.correct_answers = correct_answers_count
                attempt.score = correct_answers_count
                attempt.is_completed = True
                attempt.completed_at = timezone.now()
                attempt.save()
            if 'current_q_index' in request.session:
                del request.session['current_q_index']
            return redirect('view_result_detail', attempt_id=attempt.id)

    question = questions[current_q_index]
    answered_option_id = None
    try:
        user_answer = UserAnswer.objects.get(attempt=attempt, question=question)
        answered_option_id = user_answer.selected_option_id
    except UserAnswer.DoesNotExist:
        pass

    time_remaining_seconds = 0
    if attempt.started_at and exam.duration_minutes:
        elapsed_seconds = (timezone.now() - attempt.started_at).total_seconds()
        time_remaining_seconds = max(0, int(exam.duration_minutes * 60 - elapsed_seconds))
        logger.debug(f"exam_id={exam.id}, attempt_id={attempt.id}, started_at={attempt.started_at}, duration_minutes={exam.duration_minutes}, elapsed_seconds={elapsed_seconds}, time_remaining_seconds={time_remaining_seconds}")

    answered_question_ids = list(attempt.useranswers.all().values_list('question_id', flat=True))

    context = {
        'exam': exam,
        'question': question,
        'current_q_index': current_q_index,
        'total_questions': total_questions,
        'answered_option_id': answered_option_id,
        'time_remaining_seconds': time_remaining_seconds,
        'first_question': current_q_index == 0,
        'last_question': current_q_index == total_questions - 1,
        'attempt': attempt,
        'answered_question_ids': answered_question_ids
    }
    
    return render(request, 'test_page.html', context)

@login_required(login_url='signin')
def get_question(request):
    """ AJAX so'rovi orqali savolni qaytaradi. """
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        question_index = int(request.POST.get('current_question_index'))

        exam = get_object_or_404(Exam, id=exam_id)
        questions = exam.questions.all().order_by('id')
        total_questions = questions.count()

        if question_index < 0 or question_index >= total_questions:
            return JsonResponse({'status': 'error', 'message': 'Invalid question index.'})

        question = questions[question_index]
        attempt = get_object_or_404(UserAttempt, user=request.user, exam=exam, is_completed=False)
        
        selected_option_id = None
        try:
            answer = UserAnswer.objects.get(
                attempt=attempt,
                question=question
            )
            selected_option_id = answer.selected_option.id
        except UserAnswer.DoesNotExist:
            pass

        options_html = render_to_string('question_options.html', {'question': question, 'selected_option_id': selected_option_id})
        
        return JsonResponse({
            'status': 'success',
            'question_text': question.text,
            'question_id': question.id,
            'options_html': options_html,
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required(login_url='signin')
def submit_exam_ajax(request):
    """ AJAX so'rovi orqali javobni saqlaydi va yakunlaydi. """
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        question_id = request.POST.get('question_id')
        selected_option_id = request.POST.get('selected_option')
        
        exam = get_object_or_404(Exam, id=exam_id)
        question = get_object_or_404(Question, id=question_id)
        selected_option = get_object_or_404(AnswerOption, id=selected_option_id)
        
        attempt = get_object_or_404(UserAttempt, user=request.user, exam=exam, is_completed=False)

        with transaction.atomic():
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_option': selected_option}
            )

        # Check if the exam is complete
        total_questions = exam.questions.count()
        answered_questions_count = UserAnswer.objects.filter(attempt=attempt).count()

        is_completed = (answered_questions_count == total_questions)
        redirect_url = None

        if is_completed:
            attempt.is_completed = True
            correct_answers_count = UserAnswer.objects.filter(
                attempt=attempt,
                selected_option__is_correct=True
            ).count()
            attempt.correct_answers = correct_answers_count
            attempt.score = (correct_answers_count / total_questions) * 100 if total_questions > 0 else 0
            attempt.save()

            if 'current_question_index' in request.session:
                del request.session['current_question_index']

            redirect_url = redirect('view_result_detail', attempt_id=attempt.id).url

        return JsonResponse({
            'status': 'success',
            'is_completed': is_completed,
            'redirect_url': redirect_url
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@login_required(login_url='signin')
def student_results(request):
    """Talabaning test natijalarini ko'rish sahifasi."""
    results = UserAttempt.objects.filter(user=request.user, is_completed=True).order_by('-completed_at')
    context = {'results': results}
    return render(request, 'student_results.html', context)

@login_required(login_url='signin')
def view_result_detail(request, attempt_id):
    """ Test natijalarining batafsil ko'rinish sahifasi. """
    attempt = get_object_or_404(UserAttempt, id=attempt_id, user=request.user)
    user_answers = UserAnswer.objects.filter(attempt=attempt).order_by('question__id')
    
    total_questions = attempt.exam.questions.count()
    incorrect_answers_count = total_questions - attempt.correct_answers

    context = {
        'attempt': attempt, 
        'user_answers': user_answers,
        'incorrect_answers_count': incorrect_answers_count
    }
    return render(request, 'result_detail.html', context)


@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def create_exam(request):
    """ Yangi test yaratish sahifasi. """
    if request.method == 'POST':
        title = request.POST.get('title')
        duration = request.POST.get('duration_minutes')
        questions_ids = request.POST.getlist('questions')

        if title and duration and questions_ids:
            exam = Exam.objects.create(
                title=title,
                teacher=request.user,
                duration_minutes=duration
            )
            exam.questions.set(questions_ids)
            messages.success(request, "Yangi test muvaffaqiyatli yaratildi.")
            return redirect('my_tests')

    all_questions = Question.objects.all()
    context = {'all_questions': all_questions}
    return render(request, 'create_exam.html', context)

@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def edit_exam(request, exam_id):
    """ Mavjud testni tahrirlash sahifasi. """
    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)

    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.duration_minutes = request.POST.get('duration_minutes')
        exam.save()

        questions_ids = request.POST.getlist('questions')
        exam.questions.set(questions_ids)

        messages.success(request, "Test muvaffaqiyatli tahrirlandi.")
        return redirect('my_tests')

    all_questions = Question.objects.all()
    context = {'exam': exam, 'all_questions': all_questions}
    return render(request, 'edit_exam.html', context)


@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def delete_exam(request, exam_id):
    """ Testni o'chirish. """
    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
    exam.delete()
    messages.success(request, "Test muvaffaqiyatli o'chirildi.")
    return redirect('my_tests')


@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def teacher_results(request):
    """
    Ustoz uchun talabalar natijalarini ko'rish sahifasi.
    Barcha arifmetik amallar view ichida bajariladi.
    """
    # 1. Ustozning barcha testlarini topish
    my_exams = Exam.objects.filter(teacher=request.user)
    
    # 2. Har bir test uchun natijalarni hisoblash
    results = []
    for exam in my_exams:
        exam_data = {
            'title': exam.title,
            'attempts': []
        }
        
        # Bu testni ishlagan talabalarning urinishlarini topish
        attempts = exam.userattempt_set.all().order_by('-completed_at')
        
        for attempt in attempts:
            total_questions = exam.questions.count()
            
            # Arifmetik amallar shu yerda bajariladi
            incorrect_answers = total_questions - attempt.correct_answers
            percentage = (attempt.correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            exam_data['attempts'].append({
                'user_username': attempt.user.username,
                'correct_answers': attempt.correct_answers,
                'incorrect_answers': incorrect_answers,
                'score': attempt.score,
                'percentage': percentage,
                'completed_at': attempt.completed_at,
                'attempt_id': attempt.id
            })
        
        results.append(exam_data)
        
    context = {'results': results}
    return render(request, 'teacher_results.html', context)

@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def my_tests(request):
    """
    Ustozning o'z yaratgan testlarini ko'rish va boshqarish sahifasi.
    """
    my_exams = Exam.objects.filter(teacher=request.user).order_by('-created_at')
    context = {'my_exams': my_exams}
    return render(request, 'my_tests.html', context)


@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def my_questions(request):
    """
    Ustozning o'z savollarini ko'rish va boshqarish sahifasi.
    """
    questions = Question.objects.filter(author=request.user).order_by('-id') 
    context = {'questions': questions}
    return render(request, 'my_questions.html', context)

@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def question_form(request, question_id=None):
    """
    Yangi savol qo'shish va mavjud savolni tahrirlash uchun universal funksiya.
    """
    question = None
    if question_id:
        question = get_object_or_404(Question, id=question_id)
        if question.author != request.user:
            messages.error(request, "Siz bu savolni tahrirlash huquqiga ega emassiz.")
            return redirect('my_questions')

    if request.method == 'POST':
        # Savolni tahrirlash yoki yangi yaratish
        if question_id:
            # Tahrirlash uchun
            question.text = request.POST.get('text')
            question.question_type = request.POST.get('question_type')
            if 'image' in request.FILES:
                question.image = request.FILES['image']
            question.save()
            
            # Eski javob variantlarini o'chirish
            AnswerOption.objects.filter(question=question).delete()
            messages.success(request, "Savol muvaffaqiyatli tahrirlandi.")
        else:
            # Yangi savol yaratish uchun
            question_text = request.POST.get('text')
            image = request.FILES.get('image')
            question_type = request.POST.get('question_type')
            
            question = Question.objects.create(
                text=question_text,
                image=image,
                question_type=question_type,
                author=request.user 
            )
            messages.success(request, "Savol va javob variantlari muvaffaqiyatli qo'shildi.")

        # Javob variantlarini saqlash
        is_correct_index = request.POST.get('is_correct')
        for i in range(1, 5):
            option_text = request.POST.get(f'option_text_{i}')
            if option_text:
                is_correct = (str(i) == is_correct_index)
                AnswerOption.objects.create(
                    question=question,
                    text=option_text,
                    is_correct=is_correct
                )
        
        return redirect('my_questions')
    
    context = {'question': question}
    return render(request, 'add_questions.html', context)

@login_required(login_url='signin')
@user_passes_test(is_teacher, login_url='index')
def delete_question(request, question_id):
    """
    Savolni o'chirish uchun view funksiyasi.
    """
    question = get_object_or_404(Question, id=question_id)
    
    if question.author == request.user:
        question.delete()
        messages.success(request, "Savol muvaffaqiyatli o'chirildi.")
    else:
        messages.error(request, "Siz bu savolni o'chira olmaysiz.")
    
    return redirect('my_questions')

@login_required(login_url='signin')
def profile(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')

        user.save()
        messages.success(request, "Profilingiz muvaffaqiyatli yangilandi.")
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})


@login_required(login_url='signin')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        if not request.user.check_password(old_password):
            messages.error(request, "Joriy parol noto'g'ri.")
        elif new_password != new_password_confirm:
            messages.error(request, "Yangi parollar bir-biriga mos kelmadi.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Parolingiz muvaffaqiyatli o'zgartirildi.")
            # Parol o'zgargandan so'ng qayta kirish
            logout(request)
            return redirect('signin')

    return render(request, 'change_password.html')  # Yangi sahifa