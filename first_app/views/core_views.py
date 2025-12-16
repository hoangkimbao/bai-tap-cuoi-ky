from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from ..forms import ContactForm
from ..models import Services, Part


# Create your views here.
def index(request):
    context = {
        'message': 'Chao mung banj den voi trang quan ly garage!'
    }
    return render(request, 'index.html', context)


def services(request):
    all_services = Services.objects.all().order_by('name')
    context = {
        'danh_sach_dich_vu': all_services,
    }
    return render(request, 'services.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cảm ơn bạn đã liên hệ với chúng tôi ')
            return redirect('contact')
    else:
        form = ContactForm()
    context = {
        'form': form
    }
    return render(request, 'contact.html', context)


def search(request):
    # 1. Lấy từ khóa người dùng gõ vào (biến 'q')
    query = request.GET.get('q')

    services_results = []
    parts_results = []

    if query:
        # 2. Tìm trong Dịch Vụ (Tìm theo Tên hoặc Mô tả)
        services_results = Services.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

        # 3. Tìm trong Phụ Tùng (Tìm theo Tên, Mã SP, hoặc Thương hiệu)
        parts_results = Part.objects.filter(
            Q(name__icontains=query) |
            Q(part_number__icontains=query) |
            Q(brand__icontains=query)
        )

    context = {
        'query': query,
        'services_results': services_results,
        'parts_results': parts_results,
    }
    return render(request, 'search_results.html', context)


def service_detail(request, slug):
    """
    Hiển thị chi tiết một dịch vụ cụ thể dựa vào slug.
    """
    service = get_object_or_404(Services, slug=slug)
    context = {
        'service': service,
    }
    return render(request, 'service_detail.html', context)
