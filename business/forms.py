from django import forms
from business.models import Business, Branch, Service, Operator
from user.models import MyUser, UserTypes


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['title', 'about', 'logo']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Biznes nomi', 'class': 'form-control'}),
            'about': forms.Textarea(attrs={'placeholder': 'Biznes haqida...', 'class': 'form-control', 'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['title', 'description', 'location', 'is_active']
        widgets = {
            'title':       forms.TextInput(attrs={'placeholder': 'Filial nomi', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'placeholder': 'Filial haqida...', 'class': 'form-control', 'rows': 2}),
            'location':    forms.TextInput(attrs={'placeholder': 'Manzil', 'class': 'form-control'}),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'requirements',
                  'estimated_time_minutes', 'price', 'ticket_prefix', 'status']
        widgets = {
            'title':                  forms.TextInput(attrs={'placeholder': 'Xizmat nomi', 'class': 'form-control'}),
            'description':            forms.Textarea(attrs={'placeholder': 'Xizmat haqida...', 'class': 'form-control', 'rows': 2}),
            'requirements':           forms.Textarea(attrs={'placeholder': 'Talab qilinadigan hujjatlar...', 'class': 'form-control', 'rows': 2}),
            'estimated_time_minutes': forms.NumberInput(attrs={'placeholder': '10', 'class': 'form-control', 'min': 1}),
            'price':                  forms.NumberInput(attrs={'placeholder': '0', 'class': 'form-control', 'min': 0}),
            'ticket_prefix':          forms.TextInput(attrs={'placeholder': 'A', 'class': 'form-control', 'maxlength': 5}),
            'status':                 forms.Select(attrs={'class': 'form-control'}),
        }


class OperatorCreateForm(forms.Form):
    """Operator yaratish: yangi user + operator profili bir vaqtda"""
    first_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}))
    phone       = forms.CharField(max_length=15,  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998901234567'}))
    password    = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol'}))
    branch      = forms.ModelChoiceField(queryset=Branch.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    desk_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1'}))
    services    = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            branches = Branch.objects.filter(business=business)
            self.fields['branch'].queryset = branches
            self.fields['services'].queryset = Service.objects.filter(branch__in=branches)

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '')
        if MyUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")
        return phone

    def save(self, business):
        data = self.cleaned_data
        user = MyUser.objects.create_user(
            phone=data['phone'],
            password=data['password'],
            first_name=data['first_name'],
            user_type=UserTypes.OPERATOR,
        )
        operator = Operator.objects.create(
            user=user,
            branch=data['branch'],
            desk_number=data['desk_number'],
        )
        if data.get('services'):
            operator.services.set(data['services'])
        return operator


class OperatorEditForm(forms.ModelForm):
    class Meta:
        model = Operator
        fields = ['branch', 'desk_number', 'services', 'is_active']
        widgets = {
            'branch':      forms.Select(attrs={'class': 'form-control'}),
            'desk_number': forms.TextInput(attrs={'class': 'form-control'}),
            'services':    forms.CheckboxSelectMultiple(),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            branches = Branch.objects.filter(business=business)
            self.fields['branch'].queryset = branches
            self.fields['services'].queryset = Service.objects.filter(branch__in=branches)