import colander
import deform.widget

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('substanced')

@colander.deferred
def deferred_csrf_value(node, kw):
    return kw['request'].session.get_csrf_token()

@colander.deferred
def deferred_csrf_validator(node, kw):
    def csrf_validate(node, value):
        if value != kw['request'].session.get_csrf_token():
            raise colander.Invalid(node,
                                   _('Invalid cross-site scripting token'))
    return csrf_validate
    
class Schema(colander.Schema):
    """
    Schema base class which generates and validates a CSRF token
    automatically.  You must use it like so:

    .. code-block:: python

      from substanced.schema import CSRFSchema
      import colander

      class MySchema(CRSFSchema):
          my_value = colander.SchemaNode(colander.String())

      And in your application code, *bind* the schema, passing the request
      as a keyword argument:

      .. code-block:: python

        def aview(request):
            schema = MySchema().bind(request=request)

      In order for the CRSFSchema to work, you must configure a *session
      factory* in your Pyramid application.
    """
    _csrf_token_ = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.HiddenWidget(),
        default=deferred_csrf_value,
        validator=deferred_csrf_validator,
        )

    