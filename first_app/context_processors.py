# first_app/context_processors.py

# 1. Nhớ thêm PartGroup vào dòng import
from .models import Services, PartGroup
from .cart import Cart

def global_services_list(request):
    # Lấy tất cả dịch vụ
    all_services = Services.objects.all().order_by('name')

    # Lấy tất cả Nhóm Cha (PartGroup)
    # prefetch_related('categories') giúp lấy sẵn các con để dùng trong menu đa cấp
    all_part_groups = PartGroup.objects.prefetch_related('categories').all()

    return {
        'all_global_services': all_services,
        'all_part_groups': all_part_groups,  # Gửi danh sách Nhóm đi
    }

def cart(request):
    return {'cart': Cart(request)}