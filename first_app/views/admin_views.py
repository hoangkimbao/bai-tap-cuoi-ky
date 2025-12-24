import json

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from ..forms import PartForm
from ..models import Appointment, Order, Part


# ===================================================================
# ======================== ADMIN/STAFF VIEWS ========================
# ===================================================================

def staff_required(user):
    return user.is_staff


@user_passes_test(staff_required)
def all_appointments(request):
    """
    Hiển thị tất cả các lịch hẹn cho admin/staff quản lý.
    """
    appointments = Appointment.objects.all().order_by('-appointment_date')
    context = {
        'appointments': appointments
    }
    return render(request, 'all_appointments.html', context)


from django.conf import settings
from django.core.mail import send_mail

@user_passes_test(staff_required)
def update_appointment_status(request, appt_id, new_status):
    """
    Cập nhật trạng thái của một lịch hẹn và gửi email thông báo.
    """
    appointment = get_object_or_404(Appointment, id=appt_id)

    # Validate the new_status to make sure it's a valid choice
    valid_statuses = [status[0] for status in Appointment.STATUS_CHOICES]
    if new_status in valid_statuses:
        appointment.status = new_status
        appointment.save()
        
        # Gửi email thông báo cho khách hàng
        try:
            subject = f'Cập nhật trạng thái lịch hẹn tại Garage - {appointment.id}'
            message = f'Chào {appointment.customer.username},\n\n' \
                      f'Trạng thái lịch hẹn của bạn cho xe {appointment.car.license_plate} ' \
                      f'đã được cập nhật thành: {appointment.get_status_display()}.\n\n' \
                      f'Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!'
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [appointment.customer.email],
                fail_silently=True,
            )
        except:
            pass
            
        messages.success(request, f"Đã cập nhật trạng thái và gửi mail cho khách hàng.")
    else:
        messages.error(request, "Trạng thái cập nhật không hợp lệ.")

    return redirect('all_appointments')


@user_passes_test(staff_required)
def revenue_dashboard(request):
    """
    Hiển thị trang tổng quan doanh thu chi tiết cho admin.
    """
    today = timezone.now().date()

    # --- Doanh thu từ Dịch vụ ---
    completed_appointments = Appointment.objects.filter(status='completed')
    services_revenue_total = completed_appointments.aggregate(total=Sum('services__price'))['total'] or 0
    services_revenue_today = completed_appointments.filter(appointment_date__date=today).aggregate(
        total=Sum('services__price'))['total'] or 0
    services_revenue_this_month = \
    completed_appointments.filter(appointment_date__year=today.year, appointment_date__month=today.month).aggregate(
        total=Sum('services__price'))['total'] or 0

    # --- Doanh thu từ Bán phụ tùng ---
    paid_orders = Order.objects.filter(paid=True)
    parts_revenue_total = paid_orders.aggregate(total=Sum('total_price'))['total'] or 0
    parts_revenue_today = paid_orders.filter(created_at__date=today).aggregate(total=Sum('total_price'))[
                              'total'] or 0
    parts_revenue_this_month = \
    paid_orders.filter(created_at__year=today.year, created_at__month=today.month).aggregate(
        total=Sum('total_price'))['total'] or 0

    # --- Tổng hợp ---
    total_revenue = services_revenue_total + parts_revenue_total
    total_revenue_today = services_revenue_today + parts_revenue_today
    total_revenue_this_month = services_revenue_this_month + parts_revenue_this_month

    # --- Dữ liệu cho biểu đồ (doanh thu 12 tháng gần nhất) ---
    # Doanh thu dịch vụ theo tháng
    service_monthly_revenue = completed_appointments.annotate(
        month=TruncMonth('appointment_date')
    ).values('month').annotate(
        total=Sum('services__price')
    ).order_by('month')

    # Doanh thu phụ tùng theo tháng
    part_monthly_revenue = paid_orders.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    # Gộp dữ liệu 2 loại doanh thu
    monthly_data = {}
    for item in service_monthly_revenue:
        if item['month']:
            month_str = item['month'].strftime('%Y-%m')
            if month_str not in monthly_data:
                monthly_data[month_str] = 0
            monthly_data[month_str] += item['total']

    for item in part_monthly_revenue:
        if item['month']:
            month_str = item['month'].strftime('%Y-%m')
            if month_str not in monthly_data:
                monthly_data[month_str] = 0
            monthly_data[month_str] += item['total']

    # Sắp xếp và chuẩn bị cho biểu đồ
    sorted_months = sorted(monthly_data.keys())
    chart_labels = [f"Tháng {m.split('-')[1]}/{m.split('-')[0]}" for m in sorted_months]
    chart_data = [float(monthly_data[m]) for m in sorted_months]

    context = {
        'services_revenue_total': services_revenue_total,
        'services_revenue_today': services_revenue_today,
        'services_revenue_this_month': services_revenue_this_month,

        'parts_revenue_total': parts_revenue_total,
        'parts_revenue_today': parts_revenue_today,
        'parts_revenue_this_month': parts_revenue_this_month,

        'total_revenue': total_revenue,
        'total_revenue_today': total_revenue_today,
        'total_revenue_this_month': total_revenue_this_month,

        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'revenue_dashboard.html', context)


# ===================================================================
# ===================== PART MANAGEMENT VIEWS =======================
# ===================================================================

@user_passes_test(staff_required)
def manage_parts(request):
    """
    Hiển thị danh sách phụ tùng để quản lý, có chức năng tìm kiếm.
    """
    query = request.GET.get('q', '')
    if query:
        parts_list = Part.objects.filter(
            Q(name__icontains=query) |
            Q(part_number__icontains=query) |
            Q(brand__icontains=query)
        ).order_by('-id')
    else:
        parts_list = Part.objects.all().order_by('-id')

    context = {
        'parts': parts_list,
        'query': query
    }
    return render(request, 'part_management.html', context)


@user_passes_test(staff_required)
def manage_part_details(request, part_id=None):
    """
    Xử lý việc thêm mới hoặc chỉnh sửa một phụ tùng.
    """
    if part_id:
        # Edit existing part
        part = get_object_or_404(Part, id=part_id)
        title = f"Chỉnh sửa Phụ tùng: {part.name}"
    else:
        # Add new part
        part = None
        title = "Thêm Phụ tùng mới"

    if request.method == 'POST':
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã lưu thông tin phụ tùng '{form.cleaned_data['name']}' thành công.")
            return redirect('manage_parts')
    else:
        form = PartForm(instance=part)

    context = {
        'form': form,
        'title': title
    }
    return render(request, 'edit_part.html', context)
