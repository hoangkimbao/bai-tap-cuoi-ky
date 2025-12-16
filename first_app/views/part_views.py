from django.shortcuts import render, get_object_or_404

from ..models import Part, PartCategory, PartGroup


def parts_by_category(request, category_id):
    # 1. Dùng cái ID nhận được để tìm xem khách đang muốn xem loại nào
    # (Ví dụ: category_id=1 -> Tìm ra loại "Bánh xe")
    category = get_object_or_404(PartCategory, id=category_id)

    # 2. Lấy tất cả phụ tùng thuộc loại đó
    parts = Part.objects.filter(category=category)

    # Lấy tất cả nhóm phụ tùng và các loại phụ tùng liên quan
    all_part_groups = PartGroup.objects.prefetch_related('categories').all()

    # 3. Gửi ra template
    context = {
        'category': category,
        'parts': parts,
        'all_part_groups': all_part_groups,  # Thêm dữ liệu nhóm phụ tùng vào context
    }
    return render(request, 'parts_list.html', context)


def all_parts(request):
    # Lấy danh sách ID của các category được chọn từ query params
    selected_category_ids = request.GET.getlist('category')

    # Lấy tất cả phụ tùng, sắp xếp cái mới nhập lên đầu (-id)
    parts = Part.objects.all().order_by('-id')

    # Nếu có category được chọn, lọc danh sách phụ tùng
    if selected_category_ids:
        parts = parts.filter(category__id__in=selected_category_ids)

    # Lấy tất cả nhóm phụ tùng và các loại phụ tùng liên quan để hiển thị sidebar
    all_part_groups = PartGroup.objects.prefetch_related('categories').all()

    # Chuyển đổi ID sang integer để template dễ so sánh
    selected_ids_int = [int(id) for id in selected_category_ids]

    # Gửi sang trang parts_list.html
    context = {
        'parts': parts,
        'all_part_groups': all_part_groups,
        'selected_category_ids': selected_ids_int,  # Gửi ID đã chọn sang template
        'category': None,  # Giữ lại để tránh lỗi template nếu có dùng
    }
    return render(request, 'parts_list.html', context)


def part_detail(request, part_id):
    part = get_object_or_404(Part, id=part_id)

    context = {

        'part': part

    }

    return render(request, 'part_detail.html', context)
