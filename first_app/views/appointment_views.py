from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from ..forms import AppointmentForm, CarForm
from ..models import Car, Appointment


@login_required
def create_appointment(request):
    if request.method == 'POST':
        # Pass the user to the form
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            # Create an appointment object but don't save to database yet
            appointment = form.save(commit=False)
            # Assign the current user to the customer field
            appointment.customer = request.user
            # Now, save the object
            appointment.save()
            # Important: You need to save the many-to-many data for the form.
            form.save_m2m()

            messages.success(request, 'Bạn đã đặt lịch thành công! Chúng tôi sẽ sớm liên hệ với bạn.')
            return redirect('index')  # Redirect to the homepage after successful booking
    else:
        # Pass the user to the form to filter cars
        form = AppointmentForm(user=request.user)

    context = {
        'form': form
    }
    return render(request, 'appointment_form.html', context)


@login_required
def my_appointments(request):
    """
    Hiển thị danh sách các lịch hẹn của người dùng đã đăng nhập.
    """
    # Lấy tất cả lịch hẹn của user hiện tại, sắp xếp theo ngày hẹn gần nhất lên đầu
    appointments = Appointment.objects.filter(customer=request.user).order_by('-appointment_date')
    context = {
        'appointments': appointments
    }
    return render(request, 'my_appointments.html', context)


@login_required
def my_cars(request):
    cars = Car.objects.filter(owner=request.user).order_by('-year')
    return render(request, 'my_cars.html', {'cars': cars})


@login_required
def manage_car(request, car_id=None):
    if car_id:
        # Editing an existing car
        car = get_object_or_404(Car, id=car_id, owner=request.user)
        title = "Chỉnh sửa thông tin xe"
    else:
        # Adding a new car
        car = None
        title = "Thêm xe mới"

    if request.method == 'POST':
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            new_car = form.save(commit=False)
            new_car.owner = request.user
            new_car.save()
            messages.success(request, f'Đã lưu thông tin xe {new_car.license_plate} thành công.')
            return redirect('my_cars')
    else:
        form = CarForm(instance=car)

    return render(request, 'car_form.html', {'form': form, 'title': title})


@login_required
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, owner=request.user)
    if request.method == 'POST':
        plate = car.license_plate
        car.delete()
        messages.success(request, f'Đã xóa xe {plate} thành công.')
        return redirect('my_cars')
    # If not POST, just show the confirmation page
    return render(request, 'car_confirm_delete.html', {'car': car})
