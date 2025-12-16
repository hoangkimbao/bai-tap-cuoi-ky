from django.contrib import admin
from .models import Services, Car, Appointment, Contact, PartCategory, Part, PartGroup, Order, OrderItem

class CarAdmin(admin.ModelAdmin):
     list_display = ('license_plate', 'brand', 'model','year','owner')
     search_fields = ('license_plate','owner__username')
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'car', 'appointment_date','status')

    list_filter = ('status','appointment_date')
    search_fields = ('customer__username','car__license_plate')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['part']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'address', 'paid',
                    'created_at', 'updated_at']
    list_filter = ['paid', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

#Model
admin.site.register(Car, CarAdmin)
admin.site.register(Services)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Contact)
admin.site.register(PartGroup)
admin.site.register(PartCategory)
admin.site.register(Part)