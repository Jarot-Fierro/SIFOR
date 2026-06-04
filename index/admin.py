from django.contrib import admin
from django.contrib.auth.hashers import make_password
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from index.models import *


# =========================
# Resources
# =========================

from import_export import resources
from .models import User

@admin.action(description="Resetear contraseña al username")
def reset_password_to_username(modeladmin, request, queryset):

    users = []

    for user in queryset:

        user.password = make_password(user.username)

        users.append(user)

    User.objects.bulk_update(users, ['password'])

class UserResource(resources.ModelResource):

    class Meta:
        model = User
        import_id_fields = ['username']

        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'establecimiento',
            'is_active',
            'is_staff',
            'is_superuser',
        )

        skip_unchanged = True
        report_skipped = True




class ChoicesResource(resources.ModelResource):
    class Meta:
        model = Choices
        import_id_fields = ['id']
        fields = (
            'id',
            'choice',
            'is_answer',
        )
        skip_unchanged = True
        report_skipped = True


class QuestionsResource(resources.ModelResource):
    class Meta:
        model = Questions
        import_id_fields = ['id']
        fields = (
            'id',
            'question',
            'question_type',
            'required',
            'score',
            'feedback',
        )
        skip_unchanged = True
        report_skipped = True


class AnswerResource(resources.ModelResource):
    class Meta:
        model = Answer
        import_id_fields = ['id']
        fields = (
            'id',
            'answer',
            'answer_to',
        )
        skip_unchanged = True
        report_skipped = True


class FormResource(resources.ModelResource):
    class Meta:
        model = Form
        import_id_fields = ['id']
        fields = (
            'id',
            'code',
            'title',
            'creator',
            'collect_email',
            'authenticated_responder',
            'is_quiz',
            'allow_view_score',
            'createdAt',
            'updatedAt',
        )
        skip_unchanged = True
        report_skipped = True


class ResponsesResource(resources.ModelResource):
    class Meta:
        model = Responses
        import_id_fields = ['id']
        fields = (
            'id',
            'response_code',
            'response_to',
            'responder',
            'responder_email',
            'responder_ip',
        )
        skip_unchanged = True
        report_skipped = True


class ComunaResource(resources.ModelResource):
    class Meta:
        model = Comuna
        import_id_fields = ['id']
        fields = (
            'id',
            'nombre',
        )
        skip_unchanged = True
        report_skipped = True


class EstablecimientoResource(resources.ModelResource):
    class Meta:
        model = Establecimiento
        import_id_fields = ['id']
        fields = (
            'id',
            'nombre',
            'alias',
            'direccion',
            'telefono',
            'comuna',
        )
        skip_unchanged = True
        report_skipped = True

class FuncionarioResource(resources.ModelResource):
    class Meta:
        model = Funcionario
        import_id_fields = ['rut']

        fields = (
            'id',
            'rut',
            'dv',
            'nombre_funcionario',
            'correo',
            'descripcion_planta',
            'descripcion_calidad_juridica',
            'genero',
            'descripcion_isapre',
            'descripcion',
            'ley',
            'numero_horas',
            'descripcion_establecimiento',
            'establecimiento',
            'fecha_nacimiento',
            'fecha_inicio_contrato',
            'fecha_termino_contrato',
            'fecha_alejamiento',
            'transitorio',
            'activo',
            'fecha_importacion',
            'ultima_actualizacion',
        )

        skip_unchanged = True
        report_skipped = True
        export_order = (
            'rut',
            'dv',
            'nombre_funcionario',
            'correo',
            'descripcion_planta',
            'descripcion_calidad_juridica',
            'genero',
            'descripcion_isapre',
            'descripcion',
            'ley',
            'numero_horas',
            'descripcion_establecimiento',
            'fecha_nacimiento',
            'fecha_inicio_contrato',
            'fecha_termino_contrato',
            'fecha_alejamiento',
            'transitorio',
            'activo',
        )




class FormTokenResource(resources.ModelResource):
    class Meta:
        model = FormToken
        import_id_fields = ['id']
        fields = ('id', 'form', 'funcionario', 'token', 'expiration_date', 'used', 'created_at')
        skip_unchanged = True
        report_skipped = True


# =========================
# Admins
# =========================

@admin.register(User)
class UserAdmin(ImportExportModelAdmin):
    resource_class = UserResource

    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "establecimiento",
        "is_staff",
        "is_active",
        "is_superuser"
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "establecimiento",
    )

    ordering = ("-id",)

    fieldsets = (
        ("Información de Usuario", {
            "fields": (
                "username",
                "password",
            )
        }),

        ("Información Personal", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "establecimiento",
            )
        }),

        ("Permisos", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),

        ("Fechas Importantes", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    actions = [
        reset_password_to_username
    ]


@admin.register(Choices)
class ChoicesAdmin(ImportExportModelAdmin):
    resource_class = ChoicesResource

    list_display = (
        "id",
        "choice",
        "is_answer",
    )

    search_fields = (
        "choice",
    )

    list_filter = (
        "is_answer",
    )

    ordering = ("-id",)


@admin.register(Questions)
class QuestionsAdmin(ImportExportModelAdmin):
    resource_class = QuestionsResource

    list_display = (
        "id",
        "question",
        "question_type",
        "required",
        "score",
    )

    search_fields = (
        "question",
    )

    list_filter = (
        "question_type",
        "required",
    )

    ordering = ("-id",)


@admin.register(Answer)
class AnswerAdmin(ImportExportModelAdmin):
    resource_class = AnswerResource

    list_display = (
        "id",
        "answer",
        "answer_to",
    )

    search_fields = (
        "answer",
        "answer_to__question",
    )

    list_filter = (
        "answer_to",
    )

    ordering = ("-id",)


@admin.register(Form)
class FormAdmin(ImportExportModelAdmin):
    resource_class = FormResource

    list_display = (
        "id",
        "title",
        "creator",
        "is_quiz",
        "collect_email",
        "collect_rut",
        "authenticated_responder",
        "createdAt",
    )

    search_fields = (
        "title",
        "creator__username",
    )

    list_filter = (
        "is_quiz",
        "collect_email",
        "collect_rut",
        "authenticated_responder",
        "allow_view_score",
    )

    ordering = ("-id",)

    filter_horizontal = (
        "questions",
    )


@admin.register(Responses)
class ResponsesAdmin(ImportExportModelAdmin):
    resource_class = ResponsesResource

    list_display = (
        "id",
        "response_code",
        "response_to",
        "responder",
        "responder_email",
        "responder_rut",
    )

    search_fields = (
        "response_code",
        "responder_email",
        "responder_rut",
    )

    list_filter = (
        "response_to",
    )

    ordering = ("-id",)

    filter_horizontal = (
        "response",
    )


@admin.register(Comuna)
class ComunaAdmin(ImportExportModelAdmin):
    resource_class = ComunaResource

    list_display = (
        "id",
        "nombre",
    )

    search_fields = (
        "nombre",
    )

    ordering = ("-id",)


@admin.register(Establecimiento)
class EstablecimientoAdmin(ImportExportModelAdmin):
    resource_class = EstablecimientoResource

    list_display = (
        "id",
        "nombre",
        "alias",
        "telefono",
        "comuna",
    )

    search_fields = (
        "nombre",
        "alias",
        "comuna__nombre",
    )

    list_filter = (
        "comuna",
    )

    ordering = ("-id",)
    autocomplete_fields = ('comuna',)

    # =========================
    # Resources
    # =========================



    # =========================
    # Admins
    # =========================

@admin.register(Funcionario)
class FuncionarioAdmin(ImportExportModelAdmin):
    resource_class = FuncionarioResource

    list_display = (
        "id",
        "rut",
        "dv",
        "nombre_funcionario",
        "correo",
        "descripcion_planta",
        "establecimiento",
        "activo",
    )

    list_display_links = ("nombre_funcionario",)

    search_fields = (
        "rut",
        "nombre_funcionario",
        "correo",
        "descripcion_establecimiento",
    )

    list_filter = (
        "establecimiento",
        "genero",
        "descripcion_planta",
        "descripcion_calidad_juridica",
        "transitorio",
        "activo",
        "ley",
    )

    ordering = ("-fecha_inicio_contrato", "nombre_funcionario")

    date_hierarchy = "fecha_inicio_contrato"

    fieldsets = (
        ("Información Personal", {
            "fields": (
                "rut",
                "dv",
                "nombre_funcionario",
                "correo",
                "genero",
                "fecha_nacimiento",
            )
        }),

        ("Información Laboral", {
            "fields": (
                "descripcion_planta",
                "descripcion_calidad_juridica",
                "ley",
                "numero_horas",
                "descripcion_establecimiento",
                "establecimiento",
                "fecha_inicio_contrato",
                "fecha_termino_contrato",
                "fecha_alejamiento",
            )
        }),

        ("Información Salud", {
            "fields": (
                "descripcion_isapre",
                "descripcion",
            )
        }),

        ("Estado", {
            "fields": (
                "transitorio",
                "activo",
            )
        }),

        ("Metadatos", {
            "fields": (
                "fecha_importacion",
                "ultima_actualizacion",
            ),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("fecha_importacion", "ultima_actualizacion")

    actions = ['activar_funcionarios', 'desactivar_funcionarios']

    @admin.action(description="Activar funcionarios seleccionados")
    def activar_funcionarios(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} funcionario(s) activado(s) correctamente.")

    @admin.action(description="Desactivar funcionarios seleccionados")
    def desactivar_funcionarios(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} funcionario(s) desactivado(s) correctamente.")




@admin.register(FormToken)
class FormTokenAdmin(ImportExportModelAdmin):
    resource_class = FormTokenResource

    list_display = (
        "id",
        "form",
        "funcionario",
        "expiration_date",
        "used",
        "created_at",
    )

    search_fields = (
        "form__title",
        "funcionario__nombre_funcionario",
        "funcionario__rut",
        "token",
    )

    list_filter = (
        "used",
        "form",
    )

    readonly_fields = ("created_at",)

    ordering = ("-id",)
