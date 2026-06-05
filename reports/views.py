from django.http import HttpResponse
from index.models import Form
from .utils import export_form_responses_to_excel, export_form_responses_to_pdf


def export_form(request, form_code):

    form = Form.objects.get(code=form_code)

    return export_form_responses_to_excel(form)


def export_pdf(request, form_code):
    form = Form.objects.get(code=form_code)
    pdf_content = export_form_responses_to_pdf(form)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{form.title}_reporte.pdf"'
    response.write(pdf_content)

    return response
