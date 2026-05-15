from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Correo electrónico", blank=True, null=True)

    establecimiento = models.ForeignKey('index.Establecimiento', on_delete=models.PROTECT, null=True,
                                        blank=True,
                                        verbose_name='Establecimiento'
                                        )

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.upper()
        if self.first_name:
            self.first_name = self.first_name.upper()

        if self.last_name:
            self.last_name = self.last_name.upper()
        if self.email:
            self.email = self.email.lower()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Choices(models.Model):
    choice = models.CharField(max_length=5000, verbose_name="Opción")
    is_answer = models.BooleanField(default=False, verbose_name="Es respuesta")

    def __str__(self):
        return self.choice

    class Meta:
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'


class Questions(models.Model):
    question = models.CharField(max_length=10000, verbose_name="Pregunta")
    question_type = models.CharField(max_length=20, verbose_name="Tipo de pregunta")
    required = models.BooleanField(default=False, verbose_name="Requerida")
    answer_key = models.CharField(max_length=5000, blank=True, verbose_name="Respuesta correcta")
    score = models.IntegerField(blank=True, default=0, verbose_name="Puntaje")
    feedback = models.CharField(max_length=5000, null=True, verbose_name="Retroalimentación")
    choices = models.ManyToManyField(Choices, related_name="choices", verbose_name="Opciones")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'


class Answer(models.Model):
    answer = models.CharField(max_length=5000, verbose_name="Respuesta")
    answer_to = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name="answer_to",
                                  verbose_name="Respuesta a")

    def __str__(self):
        return f"{self.answer_to.question} -> {self.answer}"

    class Meta:
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'


class Form(models.Model):
    code = models.CharField(max_length=30, verbose_name="Código")
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.CharField(max_length=10000, blank=True, verbose_name="Descripción")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creator", verbose_name="Creador")
    background_color = models.CharField(max_length=20, default="#d9efed", verbose_name="Color de fondo")
    text_color = models.CharField(max_length=20, default="#272124", verbose_name="Color del texto")
    collect_email = models.BooleanField(default=False, verbose_name="Recopilar correo")
    authenticated_responder = models.BooleanField(default=False, verbose_name="Requiere autenticación")
    edit_after_submit = models.BooleanField(default=False, verbose_name="Editar después de enviar")
    confirmation_message = models.CharField(max_length=10000, default="Su respuesta ha sido registrada.",
                                            verbose_name="Mensaje de confirmación")
    is_quiz = models.BooleanField(default=False, verbose_name="Es cuestionario")
    allow_view_score = models.BooleanField(default=True, verbose_name="Permitir ver puntaje")
    is_public = models.BooleanField(default=False, verbose_name="Está Publicado?")
    establecimientos = models.ManyToManyField('index.Establecimiento',blank=True,verbose_name='Establecimientos')
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updatedAt = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    questions = models.ManyToManyField(Questions, related_name="questions", verbose_name="Preguntas")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Formulario'
        verbose_name_plural = 'Formularios'


class Responses(models.Model):
    response_code = models.CharField(max_length=20, verbose_name="Código de respuesta")
    response_to = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="response_to",
                                    verbose_name="Respuesta al formulario")
    responder_ip = models.CharField(max_length=30, verbose_name="IP del participante")
    responder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responder", blank=True, null=True,
                                  verbose_name="Participante")
    responder_email = models.EmailField(blank=True, verbose_name="Correo del participante")
    response = models.ManyToManyField(Answer, related_name="response", verbose_name="Respuestas")

    def __str__(self):
        return f"Respuesta {self.response_code} - {self.response_to.title}"

    class Meta:
        verbose_name = 'Envío Formulario'
        verbose_name_plural = 'Envío Formularios'


class Comuna(models.Model):
    nombre = models.CharField(max_length=100, unique=True, null=False, verbose_name='Nombre')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'


class Establecimiento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Establecimiento')
    alias = models.CharField(max_length=100, null=True, blank=True, verbose_name='Alias del Establecimiento')
    direccion = models.CharField(max_length=200, null=True, blank=True, verbose_name='Dirección')
    telefono = models.CharField(max_length=15, null=True, blank=True, verbose_name='Teléfono')
    comuna = models.ForeignKey('index.Comuna', on_delete=models.CASCADE, verbose_name='Comuna')

    class Meta:
        verbose_name = 'Establecimiento'
        verbose_name_plural = 'Establecimientos'

    def __str__(self):
        return self.alias or self.nombre
