from django import template
register = template.Library()

@register.filter
def get_responses(responses, pk):
    return responses.response.filter(answer_to__pk = pk)

@register.filter
def is_response(responses, pk):
    for i in responses:
        # Robustez ante comas (formato viejo/test) y soporte para formato nuevo
        vals = str(i.answer).split(',')
        for v in vals:
            v = v.strip()
            if not v:
                continue
            try:
                if int(v) == int(pk):
                    return True
            except (ValueError, TypeError):
                continue
    return False
