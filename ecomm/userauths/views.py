from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from userauths.forms import UserRegisterForm, ProfileForm
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.contrib.auth import login, authenticate, logout
from userauths.models import User, Profile, LoginAttempt
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt


def register_view(request):    
    if request.method == "POST":
        form = UserRegisterForm(request.POST or None)
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists. Please use a different email.")
            return redirect('userauths:sign-up')
        if form.is_valid():
            new_user = form.save(commit=False)
            username = form.cleaned_data.get("username")
            new_user.is_active = False
            new_user.save()
            messages.success(request, f"Hey {username}, You account was created successfully.")

            # Welcome Email
            subject = "Welcome to KenyaPro by Kushpedia"
            message = "Hello " + new_user.username + "!! \n" + "Welcome to KStores!! \nThank you for visiting our website\n. We have also sent you a confirmation email, please confirm your email address. \n\nThanking You\nHenry Kuria \nCEO @Kstores Kenya"        
            from_email = settings.EMAIL_HOST_USER
            to_list = [new_user.email]

            send_mail(subject, message, from_email, to_list, fail_silently=True)
                # Activation Email
            to_list = [new_user.email]
            from_email = settings.EMAIL_HOST_USER
            current_site = get_current_site(request)
            email_subject = "Confirm your Email @ Kstores"
            message2 = render_to_string('userauths/email_confirmation.html',{
                
                'name': new_user.username,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                'token': default_token_generator.make_token(new_user)
            })

            print(f"Email Message", message2)
            email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [new_user.email],
            )
            send_mail(email_subject, message2, from_email, to_list, fail_silently=True)


            return redirect('userauths:sign-in')

    else:
        form = UserRegisterForm()


    context = {
        'form': form,
    }
    return render(request, "userauths/sign-up.html", context)

#activate user through email link
def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and default_token_generator.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request,myuser)
        messages.success(request, "Your Account has been activated!!")
        return redirect('core:index')
    else:
        return render(request,'userauths/activation_failed.html')

#forgotten password
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        # username = request.POST.get('username')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "User with this email not exist.")
            return redirect('forgot_password')

        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = request.build_absolute_uri(reverse('userauths:reset_password', kwargs={'uidb64': uid, 'token': token}))

        # Send email
        send_mail(
            "Password Reset Request",
            f"Click the link below to reset your password:\n{reset_link}",
            "noreply@kstores.com",
            [user.email],
            fail_silently=False,
        )

        messages.success(request, "A password reset link has been sent to your email.")
        return redirect('userauths:sign-in')

    return render(request, 'userauths/forgot_password.html')

# reset password
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError):
        messages.error(request, "Invalid reset link.")
        return redirect('userauths:sign-in')

    if not default_token_generator.check_token(user, token):
        messages.error(request, "The password reset link is invalid or expired.")
        return redirect('userauths:forgot_password')

    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        user.set_password(new_password)
        user.save()

        # update login attempts and user lockout status
        # Get or create LoginAttempt for the user
        login_attempt, created = LoginAttempt.objects.get_or_create(
                user=user,
                defaults={'attempts': 0}
            )
        login_attempt.attempts = 0
        login_attempt.lockout_until = None
        login_attempt.save()





        messages.success(request, "Your password has been successfully reset. You can now log in.")
        return redirect('userauths:sign-in')

    return render(request, 'userauths/reset_password.html', {'uidb64': uidb64, 'token': token})


@csrf_exempt
def login_view(request):
    """Handle user login with security features including login attempts tracking"""
    
    # Redirect if user is already logged in
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in.")
        return redirect("core:index")
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        
        # Validate input
        if not email or not password:
            messages.error(request, "Please provide both email and password.")
            return render(request, "userauths/sign-in.html")
        
        try:
            # Get user from database by email
            user_obj = User.objects.get(email=email)
            
            # Check if user account is active
            if not user_obj.is_active:
                messages.warning(
                    request, 
                    "Your account is not active. Please check your email for activation instructions or contact support."
                )
                return redirect("userauths:sign-in")
            
            # Get or create LoginAttempt for the user
            login_attempt, created = LoginAttempt.objects.get_or_create(
                user=user_obj,
                defaults={'attempts': 0}
            )
            
            # Check if account is locked
            if login_attempt.attempts >= 3:
                if login_attempt.lockout_until and timezone.now() < login_attempt.lockout_until:
                    remaining_time = login_attempt.lockout_until - timezone.now()
                    minutes = int(remaining_time.total_seconds() // 60)
                    seconds = int(remaining_time.total_seconds() % 60)
                    
                    if minutes > 0:
                        time_message = f"{minutes} minute{'s' if minutes > 1 else ''}"
                        if seconds > 0:
                            time_message += f" and {seconds} second{'s' if seconds > 1 else ''}"
                    else:
                        time_message = f"{seconds} second{'s' if seconds > 1 else ''}"
                    
                    messages.warning(
                        request, 
                        f"Account is temporarily locked. Please try again in {time_message}."
                    )
                    return redirect('userauths:sign-in')
                else:
                    # Lockout period expired, reset attempts
                    login_attempt.attempts = 0
                    login_attempt.lockout_until = None
                    login_attempt.save()
            
            # Authenticate the user
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Successful login
                login_attempt.attempts = 0
                login_attempt.lockout_until = None
                login_attempt.save()
                
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                
                # Redirect to next URL or default page
                next_url = request.GET.get("next", "core:index")
                return redirect(next_url)
            else:
                # Failed authentication
                login_attempt.attempts += 1
                
                if login_attempt.attempts >= 3:
                    # Lock the account
                    login_attempt.lockout_until = timezone.now() + timedelta(minutes=30)
                    login_attempt.save()
                    
                    messages.warning(
                        request,
                        "Account has been locked due to too many failed attempts. "
                        "Please try again after 30 minutes or reset your password."
                    )
                else:
                    attempts_remaining = 3 - login_attempt.attempts
                    login_attempt.save()
                    
                    if attempts_remaining > 0:
                        messages.warning(
                            request,
                            f"Invalid email or password. You have {attempts_remaining} "
                            f"attempt{'s' if attempts_remaining > 1 else ''} remaining."
                        )
                    else:
                        messages.warning(
                            request,
                            "Invalid email or password. Next failed attempt will lock your account."
                        )
                
                return render(request, "userauths/sign-in.html", {'email': email})
                
        except User.DoesNotExist:
            # User with this email doesn't exist
            # For security, don't reveal that the user doesn't exist
            messages.warning(request, "Invalid email or password.")
            return render(request, "userauths/sign-in.html")
            
        except Exception as e:
            # Log the exception for debugging
            print(f"Login error: {str(e)}")
            messages.error(
                request,
                "An unexpected error occurred. Please try again or contact support."
            )
            return redirect('userauths:sign-in')
    
    # GET request - show login form
    return render(request, "userauths/sign-in.html")








def logout_view(request):

    logout(request)
    messages.success(request, "You logged out.")
    return redirect("userauths:sign-in")



def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect("core:dashboard")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }

    return render(request, "userauths/profile-edit.html", context)