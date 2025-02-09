from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile


class CreateUserForm(UserCreationForm):
    nickname = forms.CharField(required=True, max_length=50, label="昵称")
    invite_code = forms.CharField(required=True, label="邀请码")

    class Meta:
        model = User
        fields = ['nickname', 'username', 'password1', 'password2', 'invite_code']

    def clean(self):
        cleaned_data = super().clean()
        invite_code = cleaned_data.get('invite_code')
        if invite_code != 'test':
            self.add_error('invite_code', '邀请码错误！')
            raise forms.ValidationError('邀请码错误！')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nickname = self.cleaned_data['nickname']

        if commit:
            user.save()
            Profile.objects.create(user=user, nickname=user.nickname)
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "用户名"
        self.fields['password1'].label = "密码"
        self.fields['password2'].label = "密码验证"


class UpdateProfileForm(forms.ModelForm):
    nickname = forms.CharField(max_length=32, label="昵称", widget=forms.TextInput(attrs={"placeholder": "昵称"}))
    avatar = forms.ImageField(label="头像", required=False)

    class Meta:
        model = Profile
        fields = ["nickname", "avatar"]