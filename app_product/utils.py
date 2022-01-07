from io import BytesIO
from io import StringIO
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.conf import settings
import os.path

def fetch_pdf_resources(uri, rel):
    import os.path
    from django.conf import settings
    path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    # path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
    # print(path)
    return path


def render_to_pdf(template_src, context_dict={}):
    template=get_template(template_src)
    html=template.render(context_dict)
    result = BytesIO()
    # result = StringIO()
    # pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    # pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-32")), result)
    # pdf = pisa.CreatePDF(StringIO(html.encode("UTF-8")),result, encoding='UTF-8', show_error_as_pdf=True)
    # pdf = pisa.pisaDocument(BytesIO(html.encode("KOI8-R")), result)
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='utf-8', link_callback=fetch_pdf_resources)
    # pdf = pisa.pisaDocument(BytesIO(html.encode("Windows-1251")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None