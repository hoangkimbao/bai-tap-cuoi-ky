import random

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail

from ..forms import MyRegistrationForm, UserUpdateForm, UserProfileForm, MyAuthenticationForm
from ..models import UserProfile


class MyLoginView(LoginView):
    """
    View xử lý trang đăng nhập.
    """
    # Tên file template bạn vừa tạo
    template_name = 'login.html'
    form_class = MyAuthenticationForm

    # URL để chuyển hướng đến sau khi đăng nhập thành công
    # 'index' là name= của trang chủ trong urls.py
    success_url = reverse_lazy('index')


class MyLogoutView(LogoutView):
    """
    View xử lý khi người dùng bấm "Đăng xuất".
    """
    # Dòng này để chuyển hướng về trang chủ sau khi logout
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def register(request):
    if request.method == "POST":
        form = MyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            avatar_img = form.cleaned_data.get('avatar')
            profile, created = UserProfile.objects.get_or_create(user=user)
            if avatar_img:
                profile.avatar = avatar_img

            otp = str(random.randint(100000, 999999))
            # Để test, in OTP ra màn hình đen
            print(f"⚠️ OTP CỦA BẠN LÀ: {otp}")

            profile.otp_code = otp
            profile.save()

            # Gửi mail (bỏ qua lỗi nếu chưa cấu hình xong)
            try:
                subject = 'Mã xác nhận đăng ký Garage'
                message = f'Mã xác nhận của bạn là: {otp}'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [user.email]
                send_mail(subject, message, email_from, recipient_list)
            except:
                pass

            request.session['verifying_user_id'] = user.id
            return redirect('verify_otp')

    else:
        form = MyRegistrationForm()

    # ⬅️ QUAN TRỌNG: Dòng này phải nằm ngoài cùng (thẳng hàng với if/else)
    return render(request, 'register.html', {'form': form})


# 2. HÀM XÁC NHẬN OTP (MỚI)
def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get('otp')
        user_id = request.session.get('verifying_user_id')

        if not user_id:
            return redirect('register')

        try:
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)

            if profile.otp_code == otp_input:
                # Mã đúng! Kích hoạt tài khoản
                user.is_active = True
                user.save()

                # Xóa OTP cho sạch
                profile.otp_code = None
                profile.save()

                # Đăng nhập luôn và về trang chủ
                login(request, user)
                request.session.pop('verifying_user_id', None)

                return redirect('index')
            else:
                return render(request, 'verify_otp.html', {'error': 'Mã xác nhận không đúng!'})

        except User.DoesNotExist:
            return redirect('register')

    return render(request, 'verify_otp.html')


def custom_logout(request):
    logout(request)  # Xóa session đăng nhập
    return redirect('index')  # Chuyển về trang chủ


@login_required
def my_profile(request):
    # Dùng get_or_create để đảm bảo user nào cũng có profile, kể cả admin
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST,
                                   request.FILES,
                                   instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Tài khoản của bạn đã được cập nhật!')
            return redirect('my_profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'my_profile.html', context)
