from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

# Create your models here.
class Services(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True, verbose_name="Slug")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    cta_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Dat lich ngay'
    )
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('service_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Xử lý slug trùng lặp
        original_slug = self.slug
        counter = 1
        
        # Tạo một queryset để kiểm tra
        queryset = Services.objects.all()
        if self.pk:
            queryset = queryset.exclude(pk=self.pk) # Loại trừ chính nó khi cập nhật
        
        # Lặp cho đến khi tìm thấy slug duy nhất
        while queryset.filter(slug=self.slug).exists():
            self.slug = f'{original_slug}-{counter}'
            counter += 1

        super().save(*args, **kwargs)
class Car(models.Model):
    license_plate = models.CharField(max_length=11, unique=True, verbose_name="Biển số xe")
    brand = models.CharField(max_length=100, verbose_name="Hãng xe")
    model = models.CharField(max_length=100, verbose_name="loai xe")
    year=  models.IntegerField()
    owner= models.ForeignKey(User, on_delete=models.CASCADE, related_name='car', verbose_name="Chu xe" )
    def __str__(self):
        return f"{self.license_plate} {self.brand} {self.model}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('confirmed', 'Đã xác nhận'),
        ('in_progress', 'Đang sửa chữa'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Khach hang")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='appointments', verbose_name="xe")
    services = models.ManyToManyField(Services, verbose_name="Dich vu cham soc khach hang")
    appointment_date = models.DateTimeField()
    notes = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Trang thai")
    def __str__(self):
        return f"Lịch hẹn của{self.customer.username} {self.appointment_date.strftime('%d/%m/%Y %H:%M')}"

class Contact(models.Model):
    name= models.CharField(max_length=100, verbose_name="Họ Tên")
    email= models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True,null=True)
    message= models.TextField(blank=True,null=True)

    def __str__(self):
        return f"Tin nhắn từ {self.name} ({self.email})"
class PartGroup(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class PartCategory(models.Model):
    group = models.ForeignKey(
        PartGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Thuộc Nhóm",
        related_name='categories'  # Để sau này từ Cha lấy được hết các Con
    )

    name = models.CharField(max_length=100, verbose_name="Tên Loại Phụ Tùng")

    class Meta:
        verbose_name = "Loại Phụ Tùng"
        verbose_name_plural = "Các Loại Phụ Tùng"

    def __str__(self):
        return self.name

class Part(models.Model):
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE, verbose_name="Loại Phụ Tùng")
    name = models.CharField(max_length=200, verbose_name="Tên Phụ Tùng")
    part_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mã SP")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Thương hiệu")
    quantity = models.IntegerField(default=0, verbose_name="Số lượng")
    price = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True, verbose_name="Giá")
    image = models.CharField(max_length=500, blank=True, null=True, verbose_name="Link Ảnh")


    class Meta:
        verbose_name = "Phụ Tùng"
        verbose_name_plural = "Các Phụ Tùng"

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="Ảnh đại diện")
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    def __str__(self):
        return self.user.username

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng'),
        ('vnpay', 'Thanh toán qua VNPay'),
    ]
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khách hàng")
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    address = models.CharField(max_length=255, verbose_name="Địa chỉ giao hàng")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú đơn hàng")
    total_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, verbose_name="Phương thức thanh toán")
    paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Các Đơn hàng"
        ordering = ('-created_at',)

    def __str__(self):
        return f'Đơn hàng {self.id}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Đơn hàng")
    part = models.ForeignKey(Part, related_name='order_items', on_delete=models.CASCADE, verbose_name="Phụ tùng")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Đơn giá")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")

    class Meta:
        verbose_name = "Mục trong đơn hàng"
        verbose_name_plural = "Các mục trong đơn hàng"

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity