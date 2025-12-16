# D:\QuanLyGarage\first_project\first_project\urls.py

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# Giữ lại auth_views của Django
from django.contrib.auth import views as auth_views

# 1. Import các modules view mới, đổi tên auth_views để tránh xung đột
from first_app.views import (
    core_views,
    auth_views as custom_auth_views,
    part_views,
    appointment_views,
    order_views,
    admin_views,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # 3. Đặt tất cả các đường dẫn của bạn Ở ĐÂY
    # Core views
    path('', core_views.index, name='index'),
    path('services/', core_views.services, name='services'),
    path('services/<slug:slug>/', core_views.service_detail, name='service_detail'),
    path('contact/', core_views.contact, name='contact'),
    path('search/', core_views.search, name='search'),

    # Appointment and Car views
    path('booking/', appointment_views.create_appointment, name='create_appointment'),
    path('my-cars/', appointment_views.my_cars, name='my_cars'),
    path('my-cars/add/', appointment_views.manage_car, name='add_car'),
    path('my-cars/edit/<int:car_id>/', appointment_views.manage_car, name='edit_car'),
    path('my-cars/delete/<int:car_id>/', appointment_views.delete_car, name='delete_car'),
    path('my-appointments/', appointment_views.my_appointments, name='my_appointments'),
    
    # Auth and Profile views (sử dụng custom_auth_views)
    path('my-profile/', custom_auth_views.my_profile, name='my_profile'),
    path('register/', custom_auth_views.register, name='register'),
    path('login/', custom_auth_views.MyLoginView.as_view(), name='login'),
    path('logout/', custom_auth_views.custom_logout, name='logout'),
    path('verify_otp', custom_auth_views.verify_otp, name='verify_otp'),

    # Password Reset URLs (sử dụng auth_views của Django)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='password_reset/password_reset_form.html',
             email_template_name='password_reset/password_reset_email.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Part and Category views
    path('parts/', part_views.all_parts, name='parts_list'),
    path('parts/<int:category_id>/', part_views.parts_by_category, name='parts_by_category'),
    # Đổi tên param để tránh xung đột với URL ở trên
    path('part/<int:part_id>/', part_views.part_detail, name='part_detail'),

    # Cart, Order and Payment URLs
    path('cart/add/<int:part_id>/', order_views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:part_id>/', order_views.remove_from_cart, name='remove_from_cart'),
    path('cart/', order_views.cart_detail, name='cart_detail'),
    path('order/create/', order_views.order_create, name='order_create'),
    path('payment/return/', order_views.payment_return, name='payment_return'),
    path('payment/ipn/', order_views.payment_ipn, name='payment_ipn'),
]
# --- ADMIN URLs ---
urlpatterns += [
    path('admin-dashboard/appointments/', admin_views.all_appointments, name='all_appointments'),
    path('admin-dashboard/appointments/update/<int:appt_id>/<str:new_status>/', admin_views.update_appointment_status, name='update_appointment_status'),
    path('admin-dashboard/revenue/', admin_views.revenue_dashboard, name='revenue_dashboard'),

    # Part Management URLs
    path('admin-dashboard/parts/', admin_views.manage_parts, name='manage_parts'),
    path('admin-dashboard/part/add/', admin_views.manage_part_details, name='add_part'),
    path('admin-dashboard/part/edit/<int:part_id>/', admin_views.manage_part_details, name='edit_part'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)