# hostel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    
   
    
    path('students/add/', views.add_student, name='add_student'),
    path('students/', views.list_students, name='list_students'),
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('student/<int:student_id>/', views.view_student, name='view_student'),
    
    path('hostels/add/', views.add_hostel, name='add_hostel'),
    path('hostels/', views.list_hostels, name='list_hostels'),
    path('hostels/edit/<int:hostel_id>/', views.edit_hostel, name='edit_hostel'),
    path('hostels/delete/<int:hostel_id>/', views.delete_hostel, name='delete_hostel'),
    path('hostels/edit/<int:hostel_id>/', views.edit_hostel, name='edit_hostel'),
    
    path('rooms/', views.list_rooms, name='list_rooms'),
    path('rooms/add/', views.add_room, name='add_room'),
    path('rooms/edit/<int:room_id>/', views.edit_room, name='edit_room'),
    path('rooms/delete/<int:room_id>/', views.delete_room, name='delete_room'),
    
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('add_notice/', views.add_notice, name='add_notice'),  # Route to create a new notice
    path('list_of_notices/', views.list_of_notices, name='list_of_notices'),
    
    path('submit_complaint/', views.submit_complaint, name='submit_complaint'),
    path('complaints/', views.list_complaints, name='list_complaints'),  # Add Complaint Management URL
    path('complaint/<int:complaint_id>/', views.view_complaint, name='view_complaint'),
    
    
    # path('meal_management/', views.meal_management, name='meal_management'),
    path('fee-management/', views.fee_management, name='fee_management'),

    path('add-payment/', views.add_payment, name='add_payment'),
    path('account-book/', views.account_book, name='account_book'),
    

    

]

