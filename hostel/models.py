from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

# Hostel Model
class Hostel(models.Model):
    Hostel_ID = models.AutoField(primary_key=True)
    Hostel_Name = models.CharField(max_length=255, unique=True)
    No_Of_Rooms = models.IntegerField(default=0)
    No_Of_Students = models.IntegerField(default=0)
    Single_Seater_Rooms = models.IntegerField(default=0)
    Two_Seater_Rooms = models.IntegerField(default=0)
    Three_Seater_Rooms = models.IntegerField(default=0)
    Six_Seater_Rooms = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if int(self.No_Of_Students) < 300:
            raise ValueError("Number of students must be at least 300.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Hostel_Name
#Room model
class Room(models.Model):
    Room_ID = models.AutoField(primary_key=True)
    Room_Type = models.CharField(max_length=255)
    Capacity = models.IntegerField()
    Location = models.CharField(max_length=255)
    Room_No = models.CharField(max_length=50, unique=True)
    Floor_No = models.IntegerField()
    Students_Alloted = models.IntegerField(default=0)
    Hostel_ID = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")

    def save(self, *args, **kwargs):
        # Ensure Capacity is set based on Room_Type
        capacity_map = {"Single Seater": 1, "Two Seater": 2, "Three Seater": 3, "Six Seater": 6}
        self.Capacity = capacity_map.get(self.Room_Type, self.Capacity)
        super().save(*args, **kwargs)

    def remaining_capacity(self):
        # This should return the correct remaining capacity
        return self.Capacity - self.Students_Alloted

    @property
    def is_available(self):
        # A room is available if there is remaining capacity
        return self.remaining_capacity() > 0

    def __str__(self):
        return f"{self.Room_No} ({self.Room_Type})"

# Student Model
class Student(models.Model):
    Room_ID = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)

    # Define fee calculation based on Room type
    @property
    def total_fee_amount(self):
        room_fees = {
            'Single Seater': 8000,
            'Two Seater': 6000,
            'Three Seater': 4000,
            'Six Seater': 3000
        }
        # Return the fee based on the room type
        return room_fees.get(self.Room_ID.Room_Type, 5000)
    
    PAYMENT_STATUS_CHOICES = [
        ('NOT_PAID', 'Not Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('FULLY_PAID', 'Fully Paid'),
    ]

    Student_ID = models.AutoField(primary_key=True)
    Registration_Number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    
    
    F_Name = models.CharField(max_length=50)
    L_Name = models.CharField(max_length=50)
    Contact_Info = models.CharField(max_length=100)
    Address = models.TextField()
    Department = models.CharField(max_length=100)
    FatherName = models.CharField(max_length=50)
    fee_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='NOT_PAID')
    mess_status = models.BooleanField(default=False)
    Room_ID = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="students")
    Hostel_ID = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="students")
    # total_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_fee_status(self):
        if self.total_paid_amount == 0:
            self.fee_status = 'NOT_PAID'
        elif self.total_paid_amount < self.total_fee_amount:
            self.fee_status = 'PARTIALLY_PAID'
        else:
            self.fee_status = 'FULLY_PAID'
        self.save()

    def calculate_remaining_fee(self):
        return max(0, self.total_fee_amount - self.total_paid_amount)

# Payment Model
class Payment(models.Model):
    pdf_file = models.FileField(upload_to='payments_pdfs/', null=True, blank=True)
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending')
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('ONLINE', 'Online'),
        ('BANK', 'Bank')
    ]

    Payment_ID = models.AutoField(primary_key=True)
    Student_ID = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    Fee_Type = models.CharField(max_length=255)
    Payment_Date = models.DateTimeField(auto_now_add=True)
    Due_Date = models.DateTimeField(null=True, blank=True)
    Amount_Paid = models.DecimalField(max_digits=10, decimal_places=2)
    Receipt_Number = models.CharField(max_length=255)
    Fee_Status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    Voucher_No = models.CharField(max_length=255, default='VOU-', null=True, blank=True)
    Payment_Mode = models.CharField(max_length=50, choices=PAYMENT_MODE_CHOICES, default='CASH')
    Installment_Number = models.IntegerField(null=True, blank=True)  # Added this field

    def save(self, *args, **kwargs):
        # Generate Voucher number if not provided
        if not self.Voucher_No or self.Voucher_No == 'VOU-':
            self.Voucher_No = f'VOU-{timezone.now().strftime("%Y%m%d")}-{self.Payment_ID}'
        
        super().save(*args, **kwargs)
        
        # Update student's payment details
        student = self.Student_ID
        student.total_paid_amount = Payment.objects.filter(Student_ID=student).aggregate(
            total=models.Sum('Amount_Paid')
        )['total'] or 0
        student.update_fee_status()


from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    # Add any other fields you want to store about the user

    def __str__(self):
        return self.user.username

class Admin(models.Model):
    
    Admin_ID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=255)
    Password = models.CharField(max_length=128)
    Email = models.EmailField()
    Contact_Information = models.CharField(max_length=255)
    Admin_Role = models.CharField(max_length=100)
    Created_At = models.DateTimeField(auto_now_add=True)
    Updated_At = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.Name


    
# NoticeBoard Model
class NoticeBoard(models.Model):
    Notice_ID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=255)
    Content = models.TextField()
    Created_At = models.DateTimeField(auto_now_add=True)
    Expiry_Date = models.DateTimeField(null=True, blank=True)
    Admin_ID = models.ForeignKey(Admin, on_delete=models.CASCADE)
    Is_Active = models.BooleanField(default=True)

    def __str__(self):
        return self.Title

# Visitors Model
class Visitors(models.Model):
    Visitor_ID = models.AutoField(primary_key=True)
    Visitor_Name = models.CharField(max_length=255)
    Contact_Info = models.CharField(max_length=255)
    Time_in = models.DateTimeField()
    Time_out = models.DateTimeField()
    Student_ID = models.ForeignKey(Student, on_delete=models.CASCADE)
    Requested_By = models.CharField(max_length=255)
    Approved_By = models.CharField(max_length=255)
    Approval_Status = models.CharField(max_length=50)
    Request_Date = models.DateTimeField()

    def __str__(self):
        return self.Visitor_Name

class Complaint(models.Model):
    Complaint_ID = models.AutoField(primary_key=True)
    Student_ID = models.ForeignKey(Student, on_delete=models.CASCADE)
    Admin_ID = models.ForeignKey(Admin, on_delete=models.CASCADE)
    Complaint_Description = models.TextField()
    Complaint_Type = models.CharField(max_length=255)
    Created_At = models.DateTimeField(auto_now_add=True)
    Updated_At = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)  # Track if complaint is read
    
    def __str__(self):
        return f"Complaint {self.Complaint_ID}"

# Mess Model
class Mess(models.Model):
    Mess_ID = models.AutoField(primary_key=True)
    Hostel_ID = models.ForeignKey(Hostel, on_delete=models.CASCADE)
    Mess_Menu = models.TextField()
    Created_At = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mess ID {self.Mess_ID}"

# Attendance Model
class Attendance(models.Model):
    Attendance_ID = models.AutoField(primary_key=True)
    Student_ID = models.ForeignKey(Student, on_delete=models.CASCADE)
    Mess_ID = models.ForeignKey(Mess, on_delete=models.CASCADE)
    Admin_ID = models.ForeignKey(Admin, on_delete=models.CASCADE)
    Date = models.DateTimeField()
    Status = models.CharField(max_length=50)

    def __str__(self):
        return f"Attendance {self.Attendance_ID}"
