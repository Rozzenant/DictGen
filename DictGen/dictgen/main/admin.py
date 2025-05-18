from django.contrib import admin
from .models import User, Task, Term, Attempt, Error, Metric, TaskTerm

# Регистрация моделей
admin.site.register(User)
admin.site.register(Task)
admin.site.register(Term)
admin.site.register(Attempt)
admin.site.register(Error)
admin.site.register(Metric)
admin.site.register(TaskTerm)