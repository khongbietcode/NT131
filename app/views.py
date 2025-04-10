from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test

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
                # Redirect based on user type
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

# Admin views
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

# User views
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
            
            user = User.objects.create_user(
                id=id,
                email=email,
                password=password
            )

            if is_admin:
                user.is_superuser = True
                user.is_staff = True
                user.save()

            messages.success(request, 'Tạo người dùng thành công')
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
        messages.success(request, 'Xóa người dùng thành công')
    except User.DoesNotExist:
        messages.error(request, 'Không tìm thấy người dùng')
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
            messages.success(request, 'Cập nhật người dùng thành công')
            return redirect('user_management')
            
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
            
    return render(request, 'app/edit_user.html', {'edit_user': user_to_edit})