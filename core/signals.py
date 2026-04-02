# core/signals.py
from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def criar_grupos(sender, **kwargs):
    if sender.name == "core":  # substitua "core" pelo nome do seu app principal
        Group.objects.get_or_create(name="RH")
        Group.objects.get_or_create(name="Insumos")
