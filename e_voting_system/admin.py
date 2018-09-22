from .models import *

# Register your models here.

from datetime import datetime

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


# def disallow_registration(modeladmin, request, queryset):
#     for election in queryset:
#         election.allow_register = False
#         election.save()
#

# disallow_registration.short_description = 'Disallow registration'


class YearListFilter(admin.SimpleListFilter):
    title = _('year')
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        return [(y, y) for y in range(datetime.now().year, datetime.now().year - 5, -1)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(start_time__year=self.value())


class ActiveListFilter(admin.SimpleListFilter):
    title = _('activity')
    parameter_name = 'activity'

    def lookups(self, request, model_admin):
        return ('y', 'Yes'), ('n', 'No')

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'y':
            return queryset.filter(start_time__lt=now, end_time__gt=now)
        elif self.value() == 'n':
            return queryset.exclude(start_time__lt=now, end_time__gt=now)


class ActiveElectionListFilter(admin.SimpleListFilter):
    title = _('activity')
    parameter_name = 'activity'

    def lookups(self, request, model_admin):
        return ('y', 'Yes'), ('n', 'No')

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'y':
            return queryset.filter(election__start_time__lt=now, election__end_time__gt=now)
        elif self.value() == 'n':
            return queryset.exclude(election__start_time__lt=now, election__end_time__gt=now)


class ActiveRegistrationListFilter(admin.SimpleListFilter):
    title = _('registration')
    parameter_name = 'register'

    def lookups(self, request, model_admin):
        return ('y', 'Yes'), ('n', 'No')

    def queryset(self, request, queryset):

        if self.value() == 'y':
            return queryset.filter(election__allow_register=True)
        elif self.value() == 'n':
            return queryset.exclude(election__allow_register=True)


class CandidateAdmin(admin.ModelAdmin):
    model = Candidate
    list_display = ('__str__', 'national_number', 'can_id', 'election', 'election_year')
    list_filter = ('election__type', ActiveElectionListFilter, ActiveRegistrationListFilter)
    search_fields = ('first_name', 'last_name', 'can_id', 'election__name', 'national_number')
    fields = ['can_id', 'first_name', 'last_name', 'father_name', 'national_number', 'gender', 'degree_of_education',
              'birthday', 'election', 'motto', 'image_tag']
    readonly_fields = (
        'first_name', 'last_name', 'national_number', 'election', 'father_name', 'birthday', 'degree_of_education',
        'can_id', 'image_tag', 'gender', 'motto')




class ElectionAdmin(admin.ModelAdmin):
    model = Election
    search_fields = ('name', 'type__type', 'id')
    list_filter = ['type', YearListFilter, ActiveListFilter]  # , 'allow_register'
    list_display = ['name', 'id', 'type', 'start_time', 'end_time', 'active', 'reg_allow', 'show_results']

    #    actions = [disallow_registration]

    def reg_allow(self, obj):
        now = timezone.now()
        return obj.register_start < now < obj.register_end

    reg_allow.boolean = True
    reg_allow.short_description = 'Register'

    # reg_allow.admin_order_field = 'reg_allow'
    def show_results(self, obj):
        return format_html(
            "<a target='_blank' href='/elections/{id}/result'><img width='16px' src='/static/ref.png'></a>", id=obj.id)

    show_results.allow_tags = True
    show_results.short_description = 'Result'


class ElectionTypeAdmin(admin.ModelAdmin):
    model = ElectionType
    list_display = ('type', 'id')
    search_fields = ['type']


class CandidateRequestAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    model = CandidateRequest
    list_display = ('__str__', 'national_number', 'election', 'election_year')
    list_filter = ('election__type',)
    search_fields = ('first_name', 'last_name', 'election__name', 'national_number')
    fields = ['can_id', 'first_name', 'last_name', 'father_name', 'national_number', 'gender', 'degree_of_education',
              'birthday', 'election', 'motto', 'image_tag']
    readonly_fields = ['image_tag']


class NewsAdmin(admin.ModelAdmin):
    model = News
    list_display = ['title', 'date']


admin.site.register(Candidate, CandidateAdmin)
admin.site.register(ElectionType, ElectionTypeAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(CandidateRequest, CandidateRequestAdmin)
admin.site.register(News, NewsAdmin)
