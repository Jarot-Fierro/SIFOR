from index.models import Form
from .utils import export_form_responses_to_excel


def export_form(request, form_code):

    form = Form.objects.get(code=form_code)

    return export_form_responses_to_excel(form)
