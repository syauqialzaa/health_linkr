from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('clinic/<int:clinic_id>/', views.clinic_detail, name='clinic_detail'),
  path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
  path('appointments/', views.appointments, name='appointments'),
  path('login/', auth_views.LoginView.as_view(template_name='login.html', next_page='home'), name='login'),
  path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
  path('signup/', views.signup, name='signup'),
  path('profile/', views.profile, name='profile'),
  path('profile/password/', views.change_password, name='change_password'),
  path('password-reset/', 
      auth_views.PasswordResetView.as_view(template_name='password_reset.html'),
      name='password_reset'
  ),
  path('password-reset/done/', 
      auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
      name='password_reset_done'
  ),
  path('password-reset-confirm/<uidb64>/<token>/', 
      auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
      name='password_reset_confirm'
  ),
  path('password-reset-complete/', 
      auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
      name='password_reset_complete'
  ),
]