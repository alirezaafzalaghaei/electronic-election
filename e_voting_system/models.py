from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.html import format_html

class ElectionType(models.Model):
    id = models.PositiveIntegerField(default=0, primary_key=True)
    type = models.CharField(max_length=30, unique=True, default='')

    def __str__(self):
        return self.type


class ElectionManager(models.Manager):
    def allow_register(self):
        now = timezone.now()
        return super(ElectionManager, self).get_queryset().filter(end_register__gt=now, start_register__lt=now)


class Election(models.Model):
    objects = models.Manager()
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default='')
    type = models.ForeignKey(ElectionType, on_delete=models.CASCADE, default=0)
    max_choice = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    register_start = models.DateTimeField(null=True)
    register_end = models.DateTimeField(null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    def __str__(self):
        return "%s %s %s" % (self.type, self.name, self.start_time.year)

    def active(self):
        return self.start_time < timezone.now() < self.end_time

    active.boolean = True

    allow_register = ElectionManager()

    # def allow_register(self):
    #     return self.start_register < timezone.now() < self.end_register

    allow_register.boolean = True

    def save(self, *args, **kwargs):
        if self.end_time > self.start_time > self.register_end > self.register_start:
            super(Election, self).save(*args, **kwargs)
        else:
            raise ValueError("end_time > start_time > register_end > register_start")


DEGREES = (('BSC', 'لیسانس'), ('MSC', 'فوق لیسانس'), ('PHD', 'دکترا'))


def limit_to():
    now = timezone.now()
    return {'register_start__lt': now, 'register_end__gt': now}


class Candidate(models.Model):
    first_name = models.CharField(max_length=20, default='')
    last_name = models.CharField(max_length=20, default='')
    father_name = models.CharField(max_length=20, default='')
    birthday = models.DateField(null=True)
    degree_of_education = models.CharField(max_length=3, choices=DEGREES, default=None)
    can_id = models.PositiveIntegerField(default=0)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, limit_choices_to=limit_to)
    national_number = models.CharField(max_length=10, validators=[MinLengthValidator(10)], default='')
    motto = models.CharField(max_length=512, default='')
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], default='M', null=True)
    pic = models.ImageField(upload_to='pics', default='pics/unknown.png')

    def election_year(self):
        return str(self.election.start_time.year)

    class Meta:
        unique_together = ("can_id", "election")

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def image_tag(self):
        return format_html('<img src="/media/%s" width="150" height="150" />' % self.pic)

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


class Vote(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True)


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ("user", "election")


class CandidateRequest(models.Model):
    first_name = models.CharField(max_length=20, default='')
    last_name = models.CharField(max_length=20, default='')
    father_name = models.CharField(max_length=20, default='')
    birthday = models.DateField(null=True)
    degree_of_education = models.CharField(max_length=3, choices=DEGREES, default=None)
    can_id = models.PositiveIntegerField(null=True, default=0)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, limit_choices_to=limit_to)
    national_number = models.CharField(max_length=10, validators=[MinLengthValidator(10)], default='')
    motto = models.CharField(max_length=512, default='')
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], default='M')
    pic = models.ImageField(upload_to='pics', default='pics/unknown.png')

    class Meta:
        unique_together = ("can_id", "election")

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def election_year(self):
        return str(self.election.start_time.year)

    def image_tag(self):
        return format_html('<img src="/media/%s" width="150" height="150" />' % self.pic)

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


@receiver(post_save, sender=CandidateRequest)
def accept_candidate(sender, **kwargs):
    sndr = kwargs['instance']

    if hasattr(sndr, 'can_id') and getattr(sndr, 'can_id') is not None and int(sndr.can_id) != 0:
        if Candidate.objects.filter(election_id=sndr.election.id, can_id=sndr.can_id).exists():
            raise ValueError('This id in this election exists')
        Candidate(first_name=sndr.first_name, last_name=sndr.last_name, father_name=sndr.father_name,
                  birthday=sndr.birthday, degree_of_education=sndr.degree_of_education, can_id=sndr.can_id,
                  election=sndr.election, national_number=sndr.national_number).save()
        CandidateRequest.objects.filter(national_number=sndr.national_number, election=sndr.election).delete()


class News(models.Model):
    title = models.CharField(max_length=30)
    text = models.TextField()
    date = models.DateField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "News"
