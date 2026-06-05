from django import template
register = template.Library()

@register.filter
def get_response(responses, pk):
    resp = responses.response.filter(answer_to__pk = pk).first()
    return resp.answer if resp else ""