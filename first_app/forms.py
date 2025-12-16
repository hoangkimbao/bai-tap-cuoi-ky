from django import forms
# 1. Import UserCreationForm (để làm đăng ký)
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

from .models import Contact, Appointment, Car, Services, Order, Part


# --- FORM 1: LIÊN HỆ ---
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']

        labels = {
            'name': 'Họ tên của bạn',
            'email': 'Địa chỉ email của bạn',
            'phone': 'Số điện thoại của bạn',
            'message': 'Nội dung',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nguyễn Văn A', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'example@gmail.com', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': '090 xxx xxxx', 'class': 'form-control'}),
            'message': forms.Textarea(attrs={'placeholder': 'Nội dung...', 'class': 'form-control'}),
        }


# --- FORM 2: ĐĂNG KÝ (Bạn đang thiếu cái này) ---
class MyRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email xác nhận")
    avatar = forms.ImageField(required=False, label="Ảnh đại diện")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Tên đăng nhập mong muốn'}
        )
        self.fields['email'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'your@email.com'}
        )
        self.fields['avatar'].widget.attrs.update(
            {'class': 'form-control'}
        )
        self.fields['password1'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Nhập mật khẩu'}
        )
        self.fields['password2'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Xác nhận lại mật khẩu'}
        )

    class Meta:
        model = User
        fields = ("username", "email", "avatar")  # Thêm email và avatar vào form
        help_texts = {'username': None}

    def save(self, commit=True):
        # Lưu User trước
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Lưu thông tin phụ (Avatar) vào UserProfile
            avatar = self.cleaned_data.get('avatar')
            UserProfile.objects.create(user=user, avatar=avatar)

        return user

class MyAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Tên đăng nhập'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Mật khẩu'}
        )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)
        labels = {
            'avatar': 'Ảnh đại diện',
        }

# --- FORM 3: CẬP NHẬT THÔNG TIN USER ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Tên đăng nhập',
            'email': 'Địa chỉ email',
            'first_name': 'Tên',
            'last_name': 'Họ',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
# --- FORM 4: ĐẶT LỊCH HẸN ---
class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['car', 'services', 'appointment_date', 'notes']

        labels = {
            'car': 'Chọn xe của bạn',
            'services': 'Chọn dịch vụ mong muốn',
            'appointment_date': 'Chọn ngày và giờ hẹn',
            'notes': 'Ghi chú thêm (nếu có)',
        }

        widgets = {
            'car': forms.Select(attrs={'class': 'form-control'}),
            'services': forms.CheckboxSelectMultiple,
            'appointment_date': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local' # This will use the browser's native datetime picker
                }
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ví dụ: Xe bị rung lắc khi lên tốc độ cao...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Get the user from the view
        super(AppointmentForm, self).__init__(*args, **kwargs)
        if user:
            # Filter the 'car' dropdown to only show cars owned by the logged-in user
            self.fields['car'].queryset = Car.objects.filter(owner=user)

# --- FORM 5: THÊM/SỬA XE ---
class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['license_plate', 'brand', 'model', 'year']
        labels = {
            'license_plate': 'Biển số xe',
            'brand': 'Hãng sản xuất',
            'model': 'Tên xe (Model)',
            'year': 'Năm sản xuất',
        }
        widgets = {
            'license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: 51G-123.45'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Toyota'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Vios'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: 2022'}),
        }

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address', 'note', 'payment_method']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên đầy đủ'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ nhận hàng'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ghi chú cho đơn hàng (nếu có)'}),
            'payment_method': forms.RadioSelect,
        }
        labels = {
            'full_name': 'Họ và tên',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'address': 'Địa chỉ',
            'note': 'Ghi chú',
            'payment_method': 'Phương thức thanh toán',
        }

# --- FORM 6: QUẢN LÝ PHỤ TÙNG ---
class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['name', 'category', 'part_number', 'brand', 'quantity', 'price', 'image']
        labels = {
            'name': 'Tên phụ tùng',
            'category': 'Loại phụ tùng',
            'part_number': 'Mã phụ tùng',
            'brand': 'Thương hiệu',
            'quantity': 'Số lượng tồn kho',
            'price': 'Đơn giá (VND)',
            'image': 'URL Hình ảnh',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.URLInput(attrs={'class': 'form-control'}),
        }