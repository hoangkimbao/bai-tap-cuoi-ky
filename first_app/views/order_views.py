import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.utils.timezone import now
from django.db import transaction

from ..cart import Cart
from ..forms import OrderCreateForm
from ..models import Part, OrderItem, Order


@login_required
@require_POST
def add_to_cart(request, part_id):
    cart = Cart(request)
    part = get_object_or_404(Part, id=part_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1

    # Security check: Prevent negative or zero quantity
    if quantity <= 0:
        messages.error(request, "Số lượng phải lớn hơn 0.")
        return redirect(request.POST.get('next', 'parts_list'))

    # Logic to check stock before adding
    current_quantity_in_cart = cart.cart.get(str(part.id), {}).get('quantity', 0)

    if part.quantity <= 0:
        messages.error(request, f'Sản phẩm "{part.name}" đã hết hàng.')
    elif current_quantity_in_cart + quantity > part.quantity:
        messages.error(request, f'Không đủ hàng cho sản phẩm "{part.name}". Chỉ còn {part.quantity} sản phẩm trong kho.')
    else:
        cart.add(part=part, quantity=quantity)

    # Redirect to the page the user was on, or a default
    return redirect(request.POST.get('next', 'parts_list'))


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def remove_from_cart(request, part_id):
    cart = Cart(request)
    part = get_object_or_404(Part, id=part_id)
    cart.remove(part)
    return redirect('cart_detail')


@login_required
def order_create(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Giỏ hàng của bạn đang trống.")
        return redirect('parts_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Lưu đơn hàng ban đầu
                    order = form.save(commit=False)
                    order.customer = request.user
                    order.total_price = cart.get_total_price()
                    order.save()

                    # Lặp qua các sản phẩm trong giỏ hàng
                    for item in cart:
                        # Khóa hàng trong DB để tránh race condition
                        part_in_db = Part.objects.select_for_update().get(id=item['part'].id)

                        # Kiểm tra lại số lượng tồn kho ngay tại thời điểm xử lý
                        if part_in_db.quantity >= item['quantity']:
                            # Tạo OrderItem
                            OrderItem.objects.create(
                                order=order,
                                part=part_in_db,
                                price=item['price'],
                                quantity=item['quantity']
                            )
                            # Cập nhật số lượng
                            part_in_db.quantity -= item['quantity']
                            part_in_db.save()
                        else:
                            # Nếu không đủ hàng, báo lỗi và hủy toàn bộ giao dịch
                            messages.error(
                                request,
                                f"Rất tiếc, sản phẩm '{part_in_db.name}' đã không còn đủ số lượng. "
                                f"Vui lòng kiểm tra lại giỏ hàng."
                            )
                            # Dòng này sẽ kích hoạt rollback của transaction.atomic()
                            raise transaction.TransactionManagementError()

                # Xóa giỏ hàng chỉ khi mọi thứ thành công
                cart.clear()

                # Xử lý thanh toán
                if order.payment_method == 'vnpay':
                    vnp_TmnCode = settings.VNPAY_TMN_CODE
                    vnp_HashSecret = settings.VNPAY_HASH_SECRET_KEY
                    vnp_Url = settings.VNPAY_PAYMENT_URL
                    vnp_ReturnUrl = settings.VNPAY_RETURN_URL
                    vnp_TxnRef = f"{order.id}_{now().strftime('%Y%m%d%H%M%S')}"
                    vnp_OrderInfo = f"Thanh toan don hang {order.id}"
                    vnp_Amount = int(order.total_price) * 100
                    vnp_IpAddr = get_client_ip(request)
                    vnp_CreateDate = now().strftime('%Y%m%d%H%M%S')

                    input_data = {
                        'vnp_Version': '2.1.0',
                        'vnp_Command': 'pay',
                        'vnp_TmnCode': vnp_TmnCode,
                        'vnp_Amount': vnp_Amount,
                        'vnp_CurrCode': 'VND',
                        'vnp_TxnRef': vnp_TxnRef,
                        'vnp_OrderInfo': vnp_OrderInfo,
                        'vnp_OrderType': 'other',
                        'vnp_Locale': 'vn',
                        'vnp_ReturnUrl': vnp_ReturnUrl,
                        'vnp_IpAddr': vnp_IpAddr,
                        'vnp_CreateDate': vnp_CreateDate,
                    }
                    input_data = dict(sorted(input_data.items()))
                    hash_data = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in input_data.items()])
                    secure_hash = hmac.new(vnp_HashSecret.encode(), hash_data.encode(), hashlib.sha512).hexdigest()
                    payment_url = vnp_Url + "?" + urllib.parse.urlencode(input_data) + '&vnp_SecureHash=' + secure_hash
                    return redirect(payment_url)

                else:  # COD
                    messages.success(request, 'Đơn hàng của bạn đã được tạo thành công!')
                    return redirect('index')

            except transaction.TransactionManagementError:
                # Giao dịch đã được rollback, chỉ cần chuyển hướng người dùng
                return redirect('cart_detail')
    else:
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


def get_client_ip(request):
    """Hàm để lấy địa chỉ IP của client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def payment_return(request):
    input_data = request.GET.copy()  # Sử dụng .copy() để có thể thay đổi

    if not input_data:
        messages.error(request, "Không nhận được dữ liệu trả về từ VNPay.")
        return redirect('index')

    vnp_SecureHash = input_data.get('vnp_SecureHash')

    # Xóa các tham số không cần thiết khỏi dữ liệu để kiểm tra chữ ký
    if 'vnp_SecureHash' in input_data:
        del input_data['vnp_SecureHash']
    if 'vnp_SecureHashType' in input_data:
        del input_data['vnp_SecureHashType']

    # Sắp xếp dữ liệu theo key
    input_data = dict(sorted(input_data.items()))

    vnp_HashSecret = settings.VNPAY_HASH_SECRET_KEY

    # Tạo chuỗi hash
    hash_data = "&".join([f"{key}={urllib.parse.quote_plus(str(value))}" for key, value in input_data.items()])

    # Tạo chữ ký mới để so sánh
    secure_hash = hmac.new(vnp_HashSecret.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    # So sánh chữ ký
    if secure_hash == vnp_SecureHash:
        try:
            # Lấy mã đơn hàng từ vnp_TxnRef
            order_id_full = input_data.get('vnp_TxnRef')
            order_id_str = order_id_full.split('_')[0]
            order_id = int(order_id_str)

            order = Order.objects.get(id=order_id)

            # SECURITY CHECK: Đảm bảo người đang xem là người tạo đơn (nếu đã đăng nhập)
            # Hoặc đơn hàng không có chủ (khách vãng lai) thì thôi chấp nhận rủi ro thấp
            if request.user.is_authenticated and order.customer and order.customer != request.user:
                 return redirect('index')

            response_code = input_data.get('vnp_ResponseCode')

            # Nếu giao dịch thành công
            if response_code == '00':
                order.paid = True
                order.save()

                context = {
                    'success': True,
                    'order': order,
                    'message': 'Đơn hàng của bạn đã được thanh toán thành công!'
                }
                return render(request, 'payment_return.html', context)

            # Nếu giao dịch không thành công
            else:
                # Có thể xóa đơn hàng nếu muốn
                # order.delete()
                context = {
                    'success': False,
                    'error_message': f"Thanh toán không thành công. Mã lỗi từ VNPay: {response_code}"
                }
                return render(request, 'payment_return.html', context)

        except Order.DoesNotExist:
            context = {'success': False, 'error_message': 'Không tìm thấy đơn hàng trong hệ thống.'}
            return render(request, 'payment_return.html', context)
        except (ValueError, IndexError):
            context = {'success': False, 'error_message': 'Mã tham chiếu đơn hàng không hợp lệ.'}
            return render(request, 'payment_return.html', context)

    # Nếu chữ ký không hợp lệ
    else:
        context = {'success': False, 'error_message': 'Chữ ký không hợp lệ. Giao dịch có thể đã bị thay đổi.'}
        return render(request, 'payment_return.html', context)


@csrf_exempt
def payment_ipn(request):
    """
    View xử lý Instant Payment Notification (IPN) từ VNPay.
    """
    if request.method == 'GET':
        input_data = request.GET.copy()
        if not input_data:
            return JsonResponse({'RspCode': '99', 'Message': 'Invalid data'})

        vnp_SecureHash = input_data.get('vnp_SecureHash')

        if 'vnp_SecureHash' in input_data:
            del input_data['vnp_SecureHash']
        if 'vnp_SecureHashType' in input_data:
            del input_data['vnp_SecureHashType']

        input_data = dict(sorted(input_data.items()))

        vnp_HashSecret = settings.VNPAY_HASH_SECRET_KEY

        hash_data = "&".join([f"{key}={urllib.parse.quote_plus(str(value))}" for key, value in input_data.items()])
        secure_hash = hmac.new(vnp_HashSecret.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

        if secure_hash == vnp_SecureHash:
            try:
                order_id_full = input_data.get('vnp_TxnRef')
                order_id_str = order_id_full.split('_')[0]
                order_id = int(order_id_str)
                order = Order.objects.get(id=order_id)

                response_code = input_data.get('vnp_ResponseCode')

                # Kiểm tra xem đơn hàng đã được xử lý chưa
                if order.paid:
                    return JsonResponse({'RspCode': '02', 'Message': 'Order already confirmed'})

                # Nếu thanh toán thành công
                if response_code == '00':
                    order.paid = True
                    order.save()
                    return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
                else:
                    # Giao dịch thất bại, có thể cập nhật trạng thái đơn hàng nếu cần
                    return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})  # VNPay yêu cầu trả về 00 cho cả TH thất bại
            except Order.DoesNotExist:
                return JsonResponse({'RspCode': '01', 'Message': 'Order not found'})
            except (ValueError, IndexError):
                return JsonResponse({'RspCode': '99', 'Message': 'Invalid TxnRef'})
        else:
            return JsonResponse({'RspCode': '97', 'Message': 'Invalid Signature'})

    return JsonResponse({'RspCode': '99', 'Message': 'Invalid request method'})
