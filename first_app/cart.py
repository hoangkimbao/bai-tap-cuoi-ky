from decimal import Decimal
from django.conf import settings
from .models import Part

class Cart:
    def __init__(self, request):
        """
        Khởi tạo giỏ hàng.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Lưu một giỏ hàng rỗng vào session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, part, quantity=1, update_quantity=False):
        """
        Thêm một sản phẩm vào giỏ hàng hoặc cập nhật số lượng.
        """
        part_id = str(part.id)
        if part_id not in self.cart:
            self.cart[part_id] = {'quantity': 0, 'price': str(part.price)}

        # Kiểm tra số lượng tồn kho
        current_quantity_in_cart = self.cart[part_id]['quantity']
        if update_quantity:
            new_quantity = quantity
        else:
            new_quantity = current_quantity_in_cart + quantity

        if new_quantity > part.quantity:
            # Nếu số lượng yêu cầu vượt quá tồn kho, không làm gì cả
            # (View sẽ xử lý việc trả về thông báo lỗi)
            return False # Báo hiệu thêm vào giỏ hàng thất bại

        self.cart[part_id]['quantity'] = new_quantity
        self.save()
        return True # Báo hiệu thành công

    def save(self):
        # Đánh dấu session là "đã sửa đổi" để đảm bảo nó được lưu
        self.session.modified = True

    def remove(self, part):
        """
        Xóa một sản phẩm khỏi giỏ hàng.
        """
        part_id = str(part.id)
        if part_id in self.cart:
            del self.cart[part_id]
            self.save()

    def __iter__(self):
        """
        Lặp qua các mặt hàng trong giỏ hàng và lấy sản phẩm từ cơ sở dữ liệu.
        """
        part_ids = self.cart.keys()
        # Lấy các đối tượng sản phẩm và thêm chúng vào giỏ hàng
        parts = Part.objects.filter(id__in=part_ids)
        cart = self.cart.copy()
        for part in parts:
            cart[str(part.id)]['part'] = part
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Đếm tất cả các mặt hàng trong giỏ hàng.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Tính tổng giá của tất cả các mặt hàng trong giỏ hàng.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # Xóa giỏ hàng khỏi session
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
