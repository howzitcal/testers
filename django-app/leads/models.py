from django.db import models


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "new"),
        ("contacted", "contacted"),
        ("qualified", "qualified"),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class AuditLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=1000)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at}: {self.message}"
