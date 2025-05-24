from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
import app.mqtt_client 
from django.http import JsonResponse
from app.mqtt_client import publish_message
from app.models import CardEvent

# Store the latest received MQTT message (for demo)
latest_esp32_message = None

def is_admin(user):
    return user.is_superuser

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(request, username=user.username, password=password)
            
            if authenticated_user is not None:
                login(request, authenticated_user)
                if authenticated_user.is_superuser:
                    return redirect('admin_menu')
                else:
                    return redirect('user_menu')
            else:
                messages.error(request, 'Email hoặc mật khẩu không đúng')
        except User.DoesNotExist:
            messages.error(request, 'Email không tồn tại trong hệ thống')
    
    return render(request, 'app/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@user_passes_test(is_admin)
def admin_menu(request):
    context = {
        'total_users': User.objects.count(),
        'admin_count': User.objects.filter(is_superuser=True).count(),
        'user_count': User.objects.filter(is_superuser=False).count(),
        'user': request.user
    }
    return render(request, 'app/admin_menu.html', context)


@login_required
def user_menu(request):
    if request.user.is_superuser:
        return redirect('admin_menu')
    
    context = {
        'user': request.user
    }
    return render(request, 'app/user_menu.html', context)

@login_required
@user_passes_test(is_admin)
def user_management(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        is_admin = request.POST.get('is_admin') == 'on'

        if password != confirm_password:
            messages.error(request, 'Mật khẩu không khớp')
            return redirect('user_management')

        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Tên đăng nhập đã tồn tại')
                return redirect('user_management')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email đã tồn tại')
                return redirect('user_management')
            
            if user_id:
                if User.objects.filter(id=user_id).exists():
                    messages.error(request, 'ID đã tồn tại')
                    return redirect('user_management')
                user = User(id=user_id, username=username, email=email)
                user.set_password(password)
                user.save()
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

            if is_admin:
                user.is_superuser = True
                user.is_staff = True
                user.save()

            messages.success(request, 'Tạo nhân viên thành công')
            return redirect('user_management')

        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
            return redirect('user_management')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'app/user_management.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        if user == request.user:
            messages.error(request, 'Không thể xóa tài khoản của chính mình')
            return redirect('user_management')
        
        user.delete()
        messages.success(request, 'Xóa nhân viên thành công')
    except User.DoesNotExist:
        messages.error(request, 'Không tìm thấy nhân viên')
    return redirect('user_management')

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        is_admin = request.POST.get('is_admin') == 'on'
        
        try:
            if User.objects.exclude(id=user_id).filter(username=username).exists():
                messages.error(request, 'Tên đăng nhập đã tồn tại')
                return redirect('edit_user', user_id=user_id)

            user_to_edit.username = username
            user_to_edit.email = email
            user_to_edit.is_superuser = is_admin
            user_to_edit.is_staff = is_admin
            
            if new_password:
                user_to_edit.set_password(new_password)
            
            user_to_edit.save()
            messages.success(request, 'Cập nhật nhân viên thành công')
            return redirect('user_management')
            
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
            
    return render(request, 'app/edit_user.html', {'edit_user': user_to_edit})

@login_required
def personal_info(request):
    user = request.user
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        try:
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                messages.error(request, 'Email đã tồn tại')
                return redirect('personal_info')
            user.email = email
            if new_password:
                user.set_password(new_password)
            user.save()
            messages.success(request, 'Cập nhật thông tin thành công')
            if new_password:
                login(request, user)
            return redirect('personal_info')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    return render(request, 'app/personal_info.html', {'user': user})

@login_required
def change_password(request):
    user = request.user
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not user.check_password(old_password):
            messages.error(request, 'Mật khẩu cũ không đúng')
        elif new_password != confirm_password:
            messages.error(request, 'Mật khẩu mới không khớp')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Đổi mật khẩu thành công')
            login(request, user)
            return redirect('change_password')
    return render(request, 'app/change_password.html', {'user': user})

def mqtt_message_handler(message):
    global latest_esp32_message
    latest_esp32_message = message

# Example view to send data to ESP32
@login_required
def send_to_esp32(request):
    if request.method == 'POST':
        data = request.POST.get('data', 'Hello ESP32!')
        publish_message('esp32/data', data)
        return JsonResponse({'status': 'sent', 'data': data})
    return render(request, 'app/send_to_esp32.html')

# Example view to get the latest message from ESP32
@login_required
def get_esp32_message(request):
    return JsonResponse({'latest_message': latest_esp32_message})

@login_required
def report_view(request):
    events = CardEvent.objects.order_by('-created_at')[:50]
    return render(request, 'app/report.html', {'events': events})

@login_required
def clear_events(request):
    CardEvent.objects.all().delete()
    return redirect('report')