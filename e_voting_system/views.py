# Create your views here.

from django.contrib import auth
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import *
from .models import *


def index(request):
    return render(request, 'index.html')


def log_in(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            pin, password = form.cleaned_data.get('PIN'), form.cleaned_data.get('password')
            user = authenticate(username=pin, password=password)
            if user:
                login(request, user)
                return redirect('elections')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required(login_url='login')
def main(request):
    current_user = auth.get_user(request)
    now = timezone.now()
    all_elections = Election.objects.filter(start_time__lt=timezone.now())
    # active_elections = all_elections.filter(end_time__gt=now, start_time__lt=now)
    # notdone = active_elections.exclude(profile__user__id=current_user.id)
    done = all_elections.filter(profile__user__id=current_user.id)

    result = []
    for _election in all_elections:
        result.append(
            (_election in done, _election, _election.end_time < timezone.now(), _election.start_time > timezone.now()))
    return render(request, 'main.html', {'all': result})


@login_required(login_url='login')
def election(request, id):
    context = {}
    user = auth.get_user(request)
    this_election = Election.objects.get(id=int(id))
    if timezone.now() < this_election.start_time:
        context['result'] = 'هنوز شروع نشده'
        return render(request, 'election.html', context)
    elif not this_election.active():
        context['result'] = 'مهلت تموم شده'
        return render(request, 'election.html', context)
    if Profile.objects.filter(user=user, election=this_election).exists():
        context['result'] = 'قبلا انجام دادین'
        return render(request, 'election.html', context)
    candidates = list(Candidate.objects.filter(election_id=int(id)))
    context['info'] = [(str(x), x.motto, x.pic) for x in candidates]

    class ElectionForm(forms.Form):
        if int(this_election.max_choice) == 1:
            choices = forms.ChoiceField(choices=[(x.id, str(x)) for x in candidates], widget=forms.RadioSelect)
        else:
            choices = forms.MultipleChoiceField(choices=[(x.id, str(x)) for x in candidates],
                                                widget=forms.CheckboxSelectMultiple)

    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            choices = form.cleaned_data['choices']
            if isinstance(choices, str):  choices = [int(choices)]
            if len(choices) > int(this_election.max_choice):
                context['form'] = ElectionForm()
                context['error'] = 'بیشتر انتخاب کردی'
                context['max'] = this_election.max_choice
                return render(request, 'election.html', context)

            try:
                with transaction.atomic():
                    for code in choices:
                        candidate = Candidate.objects.get(id=code)
                        Vote(candidate=candidate, election=this_election).save()
                    Profile(user=request.user, election=this_election).save()
            except:
                context['result'] = 'یه چیزی شد نشد. نمیدونم چی شد:)'
                return render(request, 'election.html', context)
        context['result'] = 'اوکی'
        return render(request, 'election.html', context)
    else:
        context['form'] = ElectionForm()
        context['max'] = this_election.max_choice
        return render(request, 'election.html', context)


def register(request):
    now = timezone.now()

    class CandidateForm(forms.Form):
        first_name = forms.CharField(max_length=20)
        last_name = forms.CharField(max_length=20)
        father_name = forms.CharField(max_length=20)
        birthday = forms.DateField()
        degree_of_education = forms.ChoiceField(choices=DEGREES)
        election = forms.ChoiceField(
            choices=[(x.id, str(x)) for x in Election.objects.filter(register_start__lt=now, register_end__gt=now)])
        PIN = forms.CharField(max_length=10, min_length=10, required=1,
                              widget=forms.TextInput(attrs={'id': 'pin', 'placeholder': '1240032119'}))
        motto = forms.CharField(max_length=512)
        gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
        pic = forms.ImageField()

    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            fname, lname, faname, bd, dg, el, pin = form.cleaned_data['first_name'], form.cleaned_data['last_name'], \
                                                    form.cleaned_data['father_name'], form.cleaned_data['birthday'], \
                                                    form.cleaned_data['degree_of_education'], form.cleaned_data[
                                                        'election'], form.cleaned_data['PIN']
            ge, motto, pic = form.cleaned_data['gender'], form.cleaned_data['motto'], form.cleaned_data['pic']

            if Candidate.objects.filter(election_id=int(el), national_number=pin).exists():
                return render(request, 'register.html', {'result': 'قبلا ثبت نام کردی'})

            _election = Election.objects.get(id=int(el))
            CandidateRequest(first_name=fname, last_name=lname, father_name=faname, birthday=bd, degree_of_education=dg,
                             election=_election, national_number=pin, pic=pic, motto=motto, gender=ge).save()

            return render(request, 'register.html', {'result': 'اوکی. برو تایید صلاحیت شو'})
        return render(request, 'register.html', {'form': form})
    else:
        return render(request, 'register.html', {'form': CandidateForm()})


def election_result(request, id):
    this_election = Election.objects.get(id=int(id))
    if this_election.active():
        return render(request, 'result.html', {'error': 'هنوز تموم نشده'})
    if timezone.now() < this_election.start_time:
        return render(request, 'result.html', {'error': 'هنوز شروع نشده'})
    votes = Vote.objects.filter(election_id=int(id))
    candidates = Candidate.objects.filter(election_id=int(id))
    res = []
    for candidate in candidates:
        res.append((candidate, votes.filter(candidate_id=candidate.id).count()))
    return render(request, 'result.html', {'res': res})
