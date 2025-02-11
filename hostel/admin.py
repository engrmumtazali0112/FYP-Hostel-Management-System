from django.contrib import admin
from django.utils import timezone
from .models import (
    Hostel, Room, Admin, Student, Visitors, Complaint, 
    Mess, Attendance, Payment, NoticeBoard
)

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['Hostel_ID', 'Hostel_Name', 'No_Of_Rooms', 'No_Of_Students']

@admin.register(NoticeBoard)
class NoticeBoardAdmin(admin.ModelAdmin):
    list_display = ('Notice_ID', 'Title', 'Created_At', 'Expiry_Date', 'Is_Active', 'Admin_ID')
    search_fields = ('Title', 'Content')
    list_filter = ('Is_Active', 'Created_At')
    ordering = ('-Created_At',)

    def save_model(self, request, obj, form, change):
        if obj.Expiry_Date and obj.Expiry_Date < timezone.now():
            obj.Is_Active = False
        super().save_model(request, obj, form, change)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['Room_ID', 'Room_Type', 'Capacity', 'Location', 'Room_No', 'Floor_No']

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ['Admin_ID', 'Name', 'Email', 'Contact_Information', 'Admin_Role']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['Student_ID', 'F_Name', 'L_Name', 'get_email', 'Department', 'fee_status', 'get_last_payment']
    list_filter = ['fee_status', 'Department']
    search_fields = ['F_Name', 'L_Name', 'user__email']

    def get_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    get_email.short_description = 'Email'

    def get_last_payment(self, obj):
        last_payment = Payment.objects.filter(Student_ID=obj).order_by('-Payment_Date').first()
        return f"{last_payment.Amount_Paid} on {last_payment.Payment_Date.date()}" if last_payment else 'No Payment'
    get_last_payment.short_description = 'Last Payment'

@admin.register(Visitors)
class VisitorsAdmin(admin.ModelAdmin):
    list_display = ['Visitor_ID', 'Visitor_Name', 'Contact_Info', 'Time_in', 'Time_out']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['Complaint_ID', 'Student_ID', 'Admin_ID', 'Complaint_Type', 'Created_At']

@admin.register(Mess)
class MessAdmin(admin.ModelAdmin):
    list_display = ['Mess_ID', 'Hostel_ID', 'Mess_Menu', 'Created_At']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['Attendance_ID', 'Student_ID', 'Mess_ID', 'Date', 'Status']

from django.contrib import admin

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('Payment_ID', 'Student_ID', 'Fee_Type', 'Amount_Paid', 'Payment_Date', 'Fee_Status')
    list_filter = ('Fee_Status', 'Payment_Mode', 'Payment_Date')  # Changed 'status' to 'Fee_Status'
    search_fields = ('Student_ID__F_Name', 'Student_ID__L_Name', 'Fee_Type', 'Receipt_Number')