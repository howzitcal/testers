from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_q.tasks import async_task

from .forms import LeadForm
from .models import Lead


def lead_list(request):
    leads = Lead.objects.all()
    return render(request, "leads/list.html", {"leads": leads})


def lead_create(request):
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            async_task("leads.tasks.send_welcome_email", lead.id)
            messages.success(request, "Lead created; welcome email queued.")
            return redirect(reverse("lead_list"))
    else:
        form = LeadForm()
    return render(request, "leads/form.html", {"form": form, "title": "New Lead"})


def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Lead updated.")
            return redirect(reverse("lead_list"))
    else:
        form = LeadForm(instance=lead)
    return render(request, "leads/form.html", {"form": form, "title": "Edit Lead"})


def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        lead.delete()
        messages.success(request, "Lead deleted.")
    return redirect(reverse("lead_list"))
