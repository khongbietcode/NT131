from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Admin 
    path('admin-menu/', views.admin_menu, name='admin_menu'),
    path('user-management/', views.user_management, name='user_management'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    # User
    path('user-menu/', views.user_menu, name='user_menu'),
    path('personal-info/', views.personal_info, name='personal_info'),
    path('change-password/', views.change_password, name='change_password'),
    path('send-to-esp32/', views.send_to_esp32, name='send_to_esp32'),
    path('get-esp32-message/', views.get_esp32_message, name='get_esp32_message'),
    path('bao-cao-thong-ke/', views.report_view, name='report'),
    path('clear-events/', views.clear_events, name='clear_events'),
]