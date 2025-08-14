from django.urls import path
from . import views

urlpatterns = [
    # Bosh sahifalar
    path('', views.index, name='index'),
    path('tests/', views.tests, name='tests'),

    # Ro'yxatdan o'tish va kirish sahifalari
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # Talaba sahifalari
    path('student/results/', views.student_results, name='student_results'),
    path('student/results/detail/<int:attempt_id>/', views.view_result_detail, name='view_result_detail'),
    
    # Test bilan bog'liq mantig'i
    path('start-exam/<int:exam_id>/', views.start_exam, name='start_exam'),
    path('test-page/<int:exam_id>/<int:attempt_id>/', views.test_page, name='test_page'),

    # Ustoz sahifalari
    path('teacher/my-tests/', views.my_tests, name='my_tests'),
    path('teacher/exams/create/', views.create_exam, name='create_exam'),
    path('teacher/exams/edit/<int:exam_id>/', views.edit_exam, name='edit_exam'),
    path('teacher/exams/delete/<int:exam_id>/', views.delete_exam, name='delete_exam'),
    path('teacher/my-results/', views.teacher_results, name='teacher_results'),

    path('teacher/my-questions/', views.my_questions, name='my_questions'),
    # Yangi savol qo'shish uchun
    path('teacher/questions/add/', views.question_form, name='add_question'),
    # Mavjud savolni tahrirlash uchun
    path('teacher/questions/edit/<int:question_id>/', views.question_form, name='edit_question'),
    path('teacher/questions/delete/<int:question_id>/', views.delete_question, name='delete_question'),

]