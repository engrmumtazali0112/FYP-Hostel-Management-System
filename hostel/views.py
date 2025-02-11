from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Profile



#Models 
from .models import Student, Room, Hostel, NoticeBoard, Complaint, Admin, Payment

# List all hostels
def list_hostels(request):
    hostels = Hostel.objects.all()
    return render(request, 'list_hostels.html', {'hostels': hostels})


# Add a hostel and its rooms
def add_hostel(request):
    if request.method == "POST":
        hostel_name = request.POST.get("hostel_name")
        no_of_rooms = int(request.POST.get("no_of_rooms"))
        no_of_students = int(request.POST.get("no_of_students"))
        single_seater = int(request.POST.get("single_seater"))
        two_seater = int(request.POST.get("two_seater"))
        three_seater = int(request.POST.get("three_seater"))
        six_seater = int(request.POST.get("six_seater"))

        # Validate unique hostel name
        if Hostel.objects.filter(Hostel_Name=hostel_name).exists():
            messages.error(request, "Hostel name already exists!")
            return redirect("add_hostel")

        # Create hostel instance
        hostel = Hostel.objects.create(
            Hostel_Name=hostel_name,
            No_Of_Rooms=no_of_rooms,
            No_Of_Students=no_of_students,
            Single_Seater_Rooms=single_seater,
            Two_Seater_Rooms=two_seater,
            Three_Seater_Rooms=three_seater,
            Six_Seater_Rooms=six_seater,
        )
        hostel.save()

        # Create rooms for the hostel based on room types and assign sequential room numbers starting from 101
        room_types = [
            ("Single Seater", single_seater, 1),
            ("Two Seater", two_seater, 2),
            ("Three Seater", three_seater, 3),
            ("Six Seater", six_seater, 6)
        ]

        room_counter = 101  # Start room numbers from 101

        for room_type, count, capacity in room_types:
            for _ in range(count):
                # Assign room number sequentially starting from 101
                room_no = f"{room_counter}"
                room_counter += 1  # Increment room counter for next room
                
                # Ensure the room number is unique
                while Room.objects.filter(Room_No=room_no).exists():
                    room_no = f"{room_counter}"
                    room_counter += 1

                Room.objects.create(
                    Room_Type=room_type,
                    Capacity=capacity,
                    Location=hostel.Hostel_Name,
                    Room_No=room_no,
                    Floor_No=(room_counter // 10) + 1,  # Calculate floor based on room number
                    Hostel_ID=hostel,
                )

        messages.success(request, "Hostel and rooms created successfully!")
        return redirect("list_hostels")

    return render(request, 'add_hostel.html')


# Edit Hostel
def edit_hostel(request, hostel_id):
    hostel = get_object_or_404(Hostel, Hostel_ID=hostel_id)
    if request.method == 'POST':
        hostel.Hostel_Name = request.POST.get('hostel_name')
        hostel.No_Of_Rooms = request.POST.get('no_of_rooms')
        hostel.No_Of_Students = request.POST.get('no_of_students')
        hostel.Single_Seater_Rooms = request.POST.get('single_seater')
        hostel.Two_Seater_Rooms = request.POST.get('two_seater')
        hostel.Three_Seater_Rooms = request.POST.get('three_seater')
        hostel.Six_Seater_Rooms = request.POST.get('six_seater')
        hostel.save()
        messages.success(request, "Hostel updated successfully!")
        return redirect('list_hostels')
    return render(request, 'edit_hostel.html', {'hostel': hostel})

# Delete Hostel
def delete_hostel(request, hostel_id):
    hostel = get_object_or_404(Hostel, Hostel_ID=hostel_id)
    hostel.delete()
    messages.success(request, "Hostel deleted successfully!")
    return redirect('list_hostels')

def list_rooms(request):
    # Get all rooms with their related students
    rooms = Room.objects.all().prefetch_related('students')
    
    # Get search query from GET parameters
    search_query = request.GET.get('search', '')
    
    if search_query:
        rooms = rooms.filter(
            Q(Room_No__icontains=search_query) |
            Q(Room_Type__icontains=search_query) |
            Q(Location__icontains=search_query)
        )
    
    # Calculate room statistics
    for room in rooms:
        # Update remaining capacity
        room.remaining_capacity = room.Capacity - room.Students_Alloted
        room.allocated_students = room.students.all().values(
            'Student_ID',
            'F_Name',
            'L_Name',
            'Department',
            'fee_status'
        )

    context = {
        'rooms': rooms,
        'search_query': search_query,
    }
    
    return render(request, 'list_rooms.html', context)

#Add room
def add_room(request):
    if request.method == 'POST':
        hostel_id = request.POST.get('hostel_id')
        room_type = request.POST.get('room_type')
        room_no = request.POST.get('room_no')
        floor_no = request.POST.get('floor_no')
        location = request.POST.get('location')
        students_alloted = request.POST.get('students_alloted')

        # Debug: Check if the form data is being received properly
        print("Received form data:")
        print(f"Hostel ID: {hostel_id}, Room Type: {room_type}, Room No: {room_no}, Floor No: {floor_no}, Location: {location}, Students Alloted: {students_alloted}")

        # Validate form fields
        if not hostel_id or not room_type or not room_no or not floor_no or not location or not students_alloted:
            messages.error(request, "All fields are required.")
            return redirect('add_room')  # Redirect back to the form with error message

        try:
            hostel_id = int(hostel_id)
            floor_no = int(floor_no)
            students_alloted = int(students_alloted)
        except ValueError:
            messages.error(request, "Invalid input. Please enter valid integers for floor number and students allocated.")
            return redirect('add_room')

        # Fetch the selected hostel
        hostel = get_object_or_404(Hostel, pk=hostel_id)

        # Validate room type and capacity
        capacity = {"Single Seater": 1, "Two Seater": 2, "Three Seater": 3, "Six Seater": 6}.get(room_type)
        if not capacity:
            messages.error(request, "Invalid room type selected.")
            return redirect('add_room')

        # Ensure that the room does not exceed its capacity
        if students_alloted > capacity:
            messages.error(request, "Allocated students cannot exceed room capacity.")
            return redirect('add_room')

        # Check if the room number already exists
        existing_room = Room.objects.filter(Room_No=room_no, Hostel_ID=hostel).first()
        if existing_room:
            messages.error(request, f"Room number {room_no} already exists in this hostel.")
            return redirect('add_room')

        # Add the new room
        room = Room.objects.create(
            Room_No=room_no,
            Room_Type=room_type,
            Capacity=capacity,
            Location=location,
            Floor_No=floor_no,
            Students_Alloted=students_alloted,
            Hostel_ID=hostel,
        )

        # Debug: Check if room is created
        print(f"Room {room_no} created successfully in hostel {hostel.Hostel_Name}.")

        # Update the room count in the hostel
        hostel.No_Of_Rooms += 1
        hostel.save()

        messages.success(request, f"Room {room_no} added successfully!")
        return redirect('list_rooms')

    # For GET request, load hostels for selection
    hostels = Hostel.objects.all()

    return render(request, 'add_room.html', {'hostels': hostels})


# Edit Room
def edit_room(request, room_id):
    # Fetch the room or return 404 if not found
    room = get_object_or_404(Room, Room_ID=room_id)

    if request.method == 'POST':
        # Update room details from the form
        room.Room_No = request.POST.get('room_no')
        room.Room_Type = request.POST.get('room_type')
        room.Capacity = request.POST.get('capacity')
        room.Floor_No = request.POST.get('floor_no')
        room.Location = request.POST.get('location')
        room.Students_Alloted = request.POST.get('students_alloted')
        hostel_id = request.POST.get('hostel_id')

        # Get the hostel and update room details
        hostel = get_object_or_404(Hostel, Hostel_ID=hostel_id)
        room.Hostel_ID = hostel

        # Save the updated room
        room.save()

        # Update the hostel's room count
        hostel.No_Of_Rooms += 1
        hostel.save()

        # Update the room count in hostel based on room type
        hostel.update_room_count(room.Room_Type)

        messages.success(request, "Room updated successfully!")
        return redirect('list_rooms')

    # Render the edit room form
    return render(request, 'edit_room.html', {'room': room})


# Delete Room
def delete_room(request, room_id):
    room = get_object_or_404(Room, Room_ID=room_id)

    if request.method == 'POST':
        # Delete the room if confirmed
        room.delete()
        messages.success(request, "Room deleted successfully!")
        return redirect('list_rooms')

    return render(request, 'delete_room_confirmation.html', {'room': room})



def compress_image(image):
    img = Image.open(image)
    img = img.convert('RGB')
    img.thumbnail((200, 200))  # Resize to a maximum of 200x200 pixels
    
    # Save the compressed image to a BytesIO object
    output = BytesIO()
    img.save(output, format='JPEG')
    output.seek(0)
    
    return InMemoryUploadedFile(output, 'ImageField', image.name, 'image/jpeg', output.getbuffer().nbytes, None)



@login_required
def add_student(request):
    if request.method == "POST":
        email = request.POST.get("email")
        room_id = request.POST.get("room_id")
        hostel_id = request.POST.get("hostel_id")
        registration_number = request.POST.get("registration_number")  # Capture the registration number from form

        # Check if the username or email already exists
        if User.objects.filter(username=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("add_student")

        try:
            room = Room.objects.get(pk=room_id)
            hostel = Hostel.objects.get(pk=hostel_id)
        except (Room.DoesNotExist, Hostel.DoesNotExist):
            messages.error(request, "Invalid room or hostel selection.")
            return redirect("add_student")

        # Check if room has remaining capacity
        if room.remaining_capacity() <= 0:
            messages.error(request, "The selected room is full.")
            return redirect("add_student")

        # Create the user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=request.POST.get("password"),
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
        )
        user.save()

        # Process profile picture upload
        profile_picture = request.FILES.get("profile_picture")

        # Create the student
        student = Student.objects.create(
            user=user,
            F_Name=request.POST.get("first_name"),
            L_Name=request.POST.get("last_name"),
            Contact_Info=request.POST.get("contact_info"),
            Address=request.POST.get("address"),
            Department=request.POST.get("department"),
            FatherName=request.POST.get("father_name"),
            fee_status="Unpaid",  # Default status
            Room_ID=room,
            Hostel_ID=hostel,
            Registration_Number=registration_number,  # Save the registration number
            profile_picture=profile_picture  # Save the uploaded profile picture
        )

        # Increment Students_Alloted in the Room
        room.Students_Alloted += 1
        room.save()

        # Update remaining capacity when a student is added
        messages.success(request, "Student added successfully!")
        return redirect("list_students")

    hostels = Hostel.objects.all()
    rooms = Room.objects.all()
    return render(request, 'add_student.html', {'hostels': hostels, 'rooms': rooms})



@login_required
def view_student(request, student_id):
    # Get the student object based on student_id
    student = get_object_or_404(Student, Student_ID=student_id)

    return render(request, 'view_student.html', {'student': student})

@login_required
def list_students(request):
    search_query = request.GET.get('search', '')
    
    # Room type fees mapping
    room_fees = {
        'Single Seater': 8000,
        'Two Seater': 6000,
        'Three Seater': 4000,
        'Six Seater': 3000
    }
    
    students = Student.objects.all()
    
    # Calculate total fee for each student based on room type
    for student in students:
        if student.Room_ID:
            student.total_fee = room_fees.get(student.Room_ID.Room_Type, 5000)
        else:
            student.total_fee = 0
    
    if search_query:
        students = students.filter(
            Q(F_Name__icontains=search_query) |
            Q(L_Name__icontains=search_query) |
            Q(Registration_Number__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    return render(request, 'list_students.html', {
        'students': students,
        'search_query': search_query
    })
@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, Student_ID=student_id)

    if request.method == 'POST':
        # Get the previous room before changes
        previous_room = student.Room_ID

        # Update student details from form data
        student.F_Name = request.POST.get('first_name')
        student.L_Name = request.POST.get('last_name')
        student.user.email = request.POST.get('email')  # Update user email
        student.Contact_Info = request.POST.get('contact_info')
        student.Address = request.POST.get('address')
        student.Department = request.POST.get('department')
        student.FatherName = request.POST.get('father_name')
        student.fee_status = request.POST.get('fee_status')

        # Fetch room and hostel details from the form
        room_id = request.POST.get('room_id')
        hostel_id = request.POST.get('hostel_id')

        try:
            student.Room_ID = get_object_or_404(Room, Room_ID=room_id)  # Assign Room
            student.Hostel_ID = get_object_or_404(Hostel, Hostel_ID=hostel_id)  # Assign Hostel
        except (Room.DoesNotExist, Hostel.DoesNotExist):
            messages.error(request, "Invalid Room or Hostel ID selected!")
            return redirect('edit_student', student_id=student_id)

        # Update the room capacities if the room changes
        if previous_room != student.Room_ID:
            # Decrease the capacity of the previous room (remove the student)
            previous_room.Students_Alloted -= 1
            previous_room.save()

            # Increase the capacity of the new room (add the student)
            student.Room_ID.Students_Alloted += 1
            student.Room_ID.save()

        # Save the user and student details
        student.user.save()  # Save the user model
        student.save()  # Save the student model

        messages.success(request, 'Student updated successfully!')
        return redirect('list_students')

    # Render the edit student form with current student data
    hostels = Hostel.objects.all()
    rooms = Room.objects.all()

    return render(request, 'edit_student.html', {'student': student, 'hostels': hostels, 'rooms': rooms})

# Delete Student
def delete_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    room = student.Room_ID  # Get the assigned room

    if request.method == "POST":
        student.delete()  # Delete the student
        
        # Update the room allocation count
        if room:
            room.Students_Alloted = max(room.Students_Alloted - 1, 0)  # Ensure it doesn't go negative
            room.save()

        messages.success(request, "Student deleted successfully, and room availability updated!")
        return redirect("list_students")  # Redirect to student list

    return render(request, "confirm_delete.html", {"student": student})


# Login view
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to student dashboard if the user is a student
            if hasattr(user, 'student'):  # Check if the user has an associated Student profile
                return redirect('student_dashboard')
            return redirect('dashboard')  # Redirect to the general admin/dashboard page
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


# Logout view
def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect back to the login page after logout


# Registration view
def user_register(request):
    from django import forms
    from django.db import IntegrityError

    class CustomUserCreationForm(forms.Form):
        name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
        email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
        username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
        password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']

                # Create the user object
                from django.contrib.auth.models import User
                user = User.objects.create_user(username=username, email=email, password=password)
                user.first_name = name
                user.save()

                messages.success(request, "Registration successful. You can now log in.")
                return redirect('login')
            except IntegrityError:
                messages.error(request, "Username already exists. Please choose a different one.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def dashboard(request):
    total_students = Student.objects.count()
    # Fetch unread complaints count
    unread_complaints = Complaint.objects.filter(is_read=False).count()
    rooms = Room.objects.all()
    available_rooms = sum(1 for room in rooms if room.is_available)  # Count available rooms
    total_complaints = Complaint.objects.count()  # Count complaints
    
    
    active_notices = NoticeBoard.objects.filter(Is_Active=True).count()
    complaints = Complaint.objects.order_by('-Created_At')[:5]
    # Calculate the number of students who have paid their payments
    students_with_paid_payment = Payment.objects.filter(Fee_Status='PAID').values('Student_ID').distinct().count()

    context = {
        
        'total_students': total_students,
        'unread_complaints': unread_complaints,  # Add the unread complaints count
        'available_rooms': available_rooms,
        'total_complaints':total_complaints,
        'active_notices': active_notices,
        'complaints': complaints,
        'students_with_paid_payment': students_with_paid_payment,  # Number of students who have paid
        
    }

    return render(request, 'dashboard.html', context)


# Student Dashboard view
@login_required
def student_dashboard(request):
    student = Student.objects.get(user=request.user)
    
    context = {
        'student': student,
        'personal_info': {
            'Father\'s Name': student.FatherName,
            'Email': student.user.email,
            'Contact': student.Contact_Info,
            'Address': student.Address
        },
        'hostel_info': {
            'Hostel Name': student.Hostel_ID.Hostel_Name,
            'Room Number': student.Room_ID.Room_No,
            'Room Type': student.Room_ID.Room_Type,
            'Floor Number': student.Room_ID.Floor_No
        },
        'fee_status_info': [
            ('Fee Status', student.fee_status, 'green' if student.fee_status == 'Paid' else 'red'),
            ('Total Fee', f'₹{student.total_fee_amount}', 'gray'),  # This will now use the property method
            ('Paid Amount', f'₹{student.total_paid_amount}', 'gray'),
            ('Remaining Fee', f'₹{student.calculate_remaining_fee()}', 'red')
        ],
        'notices': NoticeBoard.objects.filter(Is_Active=True).order_by('-Created_At')[:5]
    }
    
    return render(request, 'student_dashboard.html', context)


# Add Notice view
@login_required
def add_notice(request):
    # Ensure the user is an admin (superuser)
    if not request.user.is_staff:
        return redirect('student_dashboard')  # Redirect non-admin users (students) to their dashboard

    # Check if the user has a profile; if not, create one
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    # Fetch the admin associated with the logged-in user
    try:
        admin = Admin.objects.get(Email=request.user.email)  # Use a valid field like 'Email' to filter
    except Admin.DoesNotExist:
        # If the admin doesn't exist, create it
        admin = Admin.objects.create(
            Name=request.user.username,  # Use the current user's name
            Admin_Role='Superuser',  # Set admin role
            Email=request.user.email,
            # Ensure the user has a profile, and use a fallback if contact_info is missing
            Contact_Information=request.user.profile.contact_info if request.user.profile.contact_info else request.user.email
        )

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        expiry_date = request.POST.get('expiry_date')

        # Create a new notice linked to the admin
        notice = NoticeBoard.objects.create(
            Title=title,
            Content=content,
            Expiry_Date=expiry_date,
            Admin_ID=admin,  # Automatically link the notice to the admin
            Is_Active=True
        )

        messages.success(request, 'Notice created successfully!')
        return redirect('add_notice')  # Redirect back to the add_notice page to show the updated list of notices

    # Fetch all active notices to display them below the form
    notices = NoticeBoard.objects.filter(Is_Active=True).order_by('-Created_At')

    return render(request, 'add_notice.html', {'notices': notices})

# List of Notices view
def list_of_notices(request):
    # Fetch all notices from the database
    notices = NoticeBoard.objects.all().order_by('-Created_At')
    return render(request, 'list_of_noticeboard.html', {'notices': notices})


# Submit Complaint view
@login_required
def submit_complaint(request):
    # Ensure the user is a student
    if not hasattr(request.user, 'student'):
        messages.error(request, "You must be a student to submit a complaint.")
        return redirect('student_dashboard')  # Redirect to student dashboard
    
    student = request.user.student  # Get the student object related to the user

    if request.method == "POST":
        complaint_description = request.POST.get('complaint_description')
        complaint_type = request.POST.get('complaint_type')

        # Fetch the first admin (or you could allow students to choose an admin if you have multiple)
        admin = Admin.objects.first()  # In real applications, choose an appropriate admin

        # Create the complaint
        Complaint.objects.create(
            Student_ID=student,
            Admin_ID=admin,
            Complaint_Description=complaint_description,
            Complaint_Type=complaint_type,
        )

        messages.success(request, "Your complaint has been submitted successfully.")
        return redirect('student_dashboard')  # Redirect back to the student dashboard

    return render(request, 'submit_complaint.html')
@login_required
def view_complaint(request, complaint_id):
    # Fetch the specific complaint using the complaint_id
    complaint = get_object_or_404(Complaint, Complaint_ID=complaint_id)

    return render(request, 'view_complaint.html', {'complaint': complaint})

# List Complaints view
# views.py

@login_required
def list_complaints(request):
    # Fetch all complaints from the database
    complaints = Complaint.objects.all().order_by('-Created_At')  # Order by creation date (latest first)

    # Mark all complaints as read when the user views them
    Complaint.objects.filter(is_read=False).update(is_read=True)
    
    # Reset the unread complaints count in the session
    request.session['unread_complaints'] = 0

    return render(request, 'list_complaints.html', {'complaints': complaints})

#All student Fee Management
@login_required
def fee_management(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('dashboard')

    # Retrieve the search query from the GET parameters.
    search_query = request.GET.get('search', '')
    
    # Start with all students.
    students = Student.objects.all()
    
    # If a search query is provided, filter the students.
    if search_query:
        students = students.filter(
            Q(F_Name__icontains=search_query) |
            Q(L_Name__icontains=search_query) |
            Q(Department__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    context = {
        'students': students,
        'search_query': search_query,
        
    }
    
    return render(request, 'fee_management.html', {'students': students})

#Add payment information
@login_required
def add_payment(request):
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to add payments.")
        return redirect('dashboard')

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        amount_paid = request.POST.get("amount_paid")
        fee_type = request.POST.get("fee_type")
        receipt_number = request.POST.get("receipt_number")
        payment_mode = request.POST.get("payment_mode")
        

        try:
            student = Student.objects.get(pk=student_id)
            
            # Get all unpaid installments
            current_year = timezone.now().year
            semesters = []
            for i in range(4):
                semesters.extend([f'Fall-{current_year + i}', f'Spring-{current_year + i + 1}'])

            # Find the first unpaid installment
            existing_payments = student.payments.all()
            paid_semesters = existing_payments.filter(Fee_Status='PAID').values_list('Fee_Type', flat=True)
            
            next_installment = None
            for semester in semesters:
                if semester not in paid_semesters:
                    next_installment = semester
                    break

            if next_installment:
                # Determine the next installment number
                install_number = len(paid_semesters) + 1
                
                # Generate voucher number
                voucher_no = f"VOU-{student.Registration_Number}-{install_number}"
                
                # Create payment record
                payment = Payment.objects.create(
                    Student_ID=student,
                    Fee_Type=next_installment,
                    Amount_Paid=amount_paid,
                    Receipt_Number=receipt_number,
                    Fee_Status="PAID",
                    Voucher_No=voucher_no,
                    Payment_Mode=payment_mode,
                    
                    Installment_Number=install_number  # Add Installment Number
                )

                messages.success(request, f"Payment of ₹{amount_paid} successfully added for {student.F_Name} {student.L_Name}")
                return redirect('fee_management')
            else:
                messages.error(request, "All installments have been paid for this student.")

        except Student.DoesNotExist:
            messages.error(request, "Student not found.")

    students = Student.objects.all()
    return render(request, 'add_payment.html', {
        'students': students,
        'payment_modes': Payment.PAYMENT_MODE_CHOICES
    })

@login_required
def remove_payment(request, payment_id):
    payment = get_object_or_404(Payment, Payment_ID=payment_id)
    student = payment.Student_ID

    # Remove the payment
    payment.delete()

    # Update the student's fee status after removing the payment
    if student.payments.filter(Fee_Status='PAID').count() == 0:
        student.fee_status = 'NOT_PAID'
    else:
        student.fee_status = 'PARTIALLY_PAID'  # Or 'FULLY_PAID' based on your logic
    student.save()

    messages.success(request, "Payment removed successfully, and fee status updated.")
    return redirect('account_book')

@login_required
def account_book(request):
    student = request.user.student
    payments = student.payments.all().order_by('Payment_Date')  # Changed from Installment_Number to Payment_Date
    
    # Get the room type fee
    room_fees = {
        'Single Seater': 8000,
        'Two Seater': 6000,
        'Three Seater': 4000,
        'Six Seater': 3000
    }
    
    total_fee = room_fees.get(student.Room_ID.Room_Type, 5000)
    per_installment = total_fee // 8
    total_paid = sum(payment.Amount_Paid for payment in payments.filter(Fee_Status='PAID'))
    remaining_fee = total_fee - total_paid
    paid_installments = payments.filter(Fee_Status='PAID').count()

    # Create semester mapping for all 8 installments
    semesters = []
    start_year = timezone.now().year
    for i in range(4):
        semesters.extend([f'Fall-{start_year + i}', f'Spring-{start_year + i + 1}'])

    # Create expected payments list with proper status tracking
    expected_payments = []
    paid_semesters = payments.filter(Fee_Status='PAID').values_list('Fee_Type', flat=True)
    
    for i, semester in enumerate(semesters[:8], 1):
        payment = payments.filter(Fee_Type=semester).first()
        
        expected_payments.append({
        'challan_no': f'{student.Registration_Number}-{i}',
        'semester': semester,
        'amount': per_installment,
        'status': 'PAID' if semester in paid_semesters else 'UNPAID',
        'voucher_no': payment.Voucher_No if payment else '',
        'payment_date': payment.Payment_Date.strftime('%Y-%m-%d') if payment else '',
        'payment_mode': payment.Payment_Mode if payment else '-'  # Changed this line
        
    })

    context = {
        'student': student,
        'total_fee': total_fee,
        'per_installment': per_installment,
        'paid_installments': f"{paid_installments}/8",
        'remaining_fee': remaining_fee,
        'payments': expected_payments
      
    }
    return render(request, 'account_book.html', context)
