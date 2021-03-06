# Copyright 2009 - 2011 Machinalis: http://www.machinalis.com/
#
# This file is part of Eff.
#
# Eff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Eff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Eff.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin
from eff_site.eff.models import Project, Client, ExternalSource, Wage, BillingEmail
from eff_site.eff.models import (AvgHours, Currency, ProjectAssoc, TimeLog,
                                 Handle, ClientHandles, Billing, CreditNote,
                                 Payment, CommercialDocumentBase)
from _models.user_profile import UserProfile
from eff_site.eff.forms import UserAdminForm, UserAdminChangeForm
from django.contrib.auth.models import User
from _models.dump import Dump
from eff_site.eff._models.external_source import ExternalId
from django import forms
from attachments.admin import AttachmentInlines
from attachments.models import Attachment


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'content_object', 'creator',
                    'attachment_file', 'created', 'modified')
    ordering = ('modified',)
    search_fields = ('content_type', 'content_object', 'creator',
                     'attachment_file', 'created', 'modified')


class TimeLogAdminForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('username'))
    dump = forms.ModelChoiceField(queryset=Dump.objects.order_by('-date'))

    class Meta:
        model = TimeLog


class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'hours_booked', 'project', 'task_name',
                    'description')
    ordering = ('date',)
    search_fields = ('task_name', 'description', 'user__username',
                     'user__first_name')
    form = TimeLogAdminForm


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'billable', 'client', 'external_id')
    ordering = ('name',)
    search_fields = ('name',)


class ProjectAssocInLine(admin.TabularInline):
    model = ProjectAssoc
    extra = 1


class ProjectAssocAdmin(admin.ModelAdmin):
    list_display = ('project', 'member', 'from_date', 'to_date', 'client_rate',
                    'user_rate', )
    ordering = ('member',)
    search_fields = ('project__name', 'member__user__username',
                     'member__user__first_name')


class ProjectsInLine(admin.TabularInline):
    model = Project
    extra = 1


class BillingEmailAdminForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.order_by('name'))

    class Meta:
        model = BillingEmail


class BillingEmailAdmin(admin.ModelAdmin):
    search_fields = ('email_address', 'client__name', )
    ordering = ('client',)
    list_display = ('client', 'email_address', 'send_as')
    list_filter = ('client', 'email_address', 'send_as')
    form = BillingEmailAdminForm


class BillingEmailsInLine(admin.TabularInline):
    model = BillingEmail
    extra = 1


class ClientAdmin(admin.ModelAdmin):
    inlines = [BillingEmailsInLine, ProjectsInLine]
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'city', 'country',
                     'currency__ccy_code', 'external_source__name',)
    ordering = ('name',)


class ExternalSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'fetch_url', 'csv_directory', 'csv_filename')
    ordering = ('name',)


class WageInLine(admin.TabularInline):
    model = Wage


class WageAdminForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('username'))

    class Meta:
        model = Wage


class WageAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount_per_hour')
    list_filter = ('date', 'amount_per_hour',)
    ordering = ('date',)
    search_fields = ('user__first_name', 'user__username',)
    form = WageAdminForm


class AvgHoursInLine(admin.TabularInline):
    model = AvgHours


class AvgHoursAdminForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('username'))

    class Meta:
        model = AvgHours


class AvgHoursAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'hours')
    list_filter = ('date', 'hours',)
    ordering = ('-date',)
    search_fields = ('user__first_name', 'user__username',)
    form = AvgHoursAdminForm


class UserProfileInLine(admin.TabularInline):
    model = UserProfile


class UserProfileAdminForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('username'))
    # Set amount of users shown at a time to 10, make an ordered query
    watches = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size': 10}),
        queryset=User.objects.order_by('username'),
        label='Users to follow', required=False)

    def clean_watches(self):
        data = self.cleaned_data['watches']
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            pass
        else:
            if admin_user in data:
                raise forms.ValidationError("Don't add admin here")

        if self.instance.user in data:
            raise forms.ValidationError("You are adding this user to watch " +\
                                        "himself, please don't")

        return data

    class Meta:
        model = UserProfile


class ClientHandlesInLine(admin.TabularInline):
    model = ClientHandles


class ExternalIdInLine(admin.TabularInline):
    model = ExternalId
    extra = 1


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'phone_number')
    ordering = ('user__username',)
    search_fields = ('user__first_name', 'user__username',)
    form = UserProfileAdminForm
    inlines = [ClientHandlesInLine, ProjectAssocInLine, ExternalIdInLine]

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = []
        if hasattr(obj, "is_client") and obj.is_client():
            self.exclude.append('personal_email')
        return super(UserProfileAdmin, self).get_form(request, obj, **kwargs)


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name')
    inlines = [WageInLine, AvgHoursInLine]
    ordering = ('username',)

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            base_form = UserAdminForm
        else:
            base_form = UserAdminChangeForm
        kwargs['form'] = base_form

        return super(UserAdmin, self).get_form(request, obj, **kwargs)

    class Media:
        js = ('/media/js/adminformFieldsValidations.js',)


class CurrencyAdmin(admin.ModelAdmin):
    pass


class ExternalIdAdmin(admin.ModelAdmin):
    list_display = ('login', 'source', 'userprofile')
    search_fields = ('userprofile__user__username',
                     'userprofile__user__first_name')
    ordering = ('userprofile',)


class HandleAdmin(admin.ModelAdmin):
    list_display = ('protocol',)


class CommercialDocumentAdminForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.order_by('name'))

    class Meta:
        model = CommercialDocumentBase


class BillingAdminForm(forms.ModelForm):
    client = forms.ModelChoiceField(queryset=Client.objects.order_by('name'))

    def __init__(self, *args, **kwargs):
        super(BillingAdminForm, self).__init__(*args, **kwargs)
        self.fields['date'].label = 'Send Date'

    class Meta:
        model = Billing


class BillingAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'date', 'expire_date', 'payment_date',
                    'concept')
    search_fields = ('client', 'date', 'concept', 'amount')
    ordering = ('client',)
    form = BillingAdminForm
    inlines = [AttachmentInlines]


class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'date', 'concept')
    search_fields = ('client', 'date', 'concept', 'amount')
    ordering = ('client',)
    form = CommercialDocumentAdminForm
    inlines = [AttachmentInlines]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'date', 'status', 'concept')
    search_fields = ('client', 'date', 'concept', 'amount', 'status')
    form = CommercialDocumentAdminForm
    inlines = [AttachmentInlines]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectAssoc, ProjectAssocAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(ExternalSource, ExternalSourceAdmin)
admin.site.register(Wage, WageAdmin)
admin.site.register(AvgHours, AvgHoursAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(ExternalId, ExternalIdAdmin)
admin.site.register(TimeLog, TimeLogAdmin)
admin.site.register(BillingEmail, BillingEmailAdmin)
admin.site.register(Handle, HandleAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(CreditNote, CreditNoteAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Attachment, AttachmentAdmin)
