import unittest
from pyramid import testing

class check_csrf_token(unittest.TestCase):
    def _callFUT(self, request, token):
        from .. import check_csrf_token
        return check_csrf_token(request, token)

    def test_success(self):
        request = testing.DummyRequest()
        request.params['csrf_token'] = request.session.get_csrf_token()
        self.assertEqual(self._callFUT(request, 'csrf_token'), None)

    def test_failure(self):
        from pyramid.httpexceptions import HTTPBadRequest
        request = testing.DummyRequest()
        self.assertRaises(HTTPBadRequest, self._callFUT, request, 'csrf_token')

class Test_add_mgmt_view(unittest.TestCase):
    def _callFUT(self, config, **kw):
        from .. import add_mgmt_view
        return add_mgmt_view(config, **kw)

    def _makeConfig(self):
        config = DummyConfigurator()
        return config

    def test_with_request_method_sorted(self):
        config = self._makeConfig()
        self._callFUT(config, request_method=('HEAD', 'GET'))
        self.assertEqual(config._added['request_method'], ('GET', 'HEAD'))
        self.assertTrue(config._actions)

    def test_with_request_method_get_implies_head(self):
        config = self._makeConfig()
        self._callFUT(config, request_method='GET')
        self.assertEqual(config._added['request_method'], ('GET', 'HEAD'))
        self.assertTrue(config._actions)

    def test_with_check_csrf(self):
        from pyramid.httpexceptions import HTTPBadRequest
        config = self._makeConfig()
        self._callFUT(config, check_csrf=True)
        preds = config._added['custom_predicates']
        self.assertEqual(len(preds), 1)
        self.assertTrue(config._actions)
        request = testing.DummyRequest()
        self.assertRaises(HTTPBadRequest, preds[0], None, request)
        request = testing.DummyRequest()
        request.params['csrf_token'] = request.session.get_csrf_token()
        self.assertTrue(preds[0](None, request))

    def test_view_isclass_with_attr(self):
        class AView(object):
            pass
        config = self._makeConfig()
        self._callFUT(config, view=AView, attr='foo')
        self.assertTrue(config.desc.startswith('method'))

    def test_discriminator(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertTrue(config._actions[0][0], 'sdi view')

    def test_intr_action(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._actions[0][1][0], config._intr)

    def test_intr_related(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertTrue('views' in config._intr.related)

    def test_intr_values(self):
        config = self._makeConfig()
        self._callFUT(
            config, tab_title='tab_title', tab_condition='tab_condition',
            check_csrf=True, csrf_token='csrf_token')
        self.assertEqual(config._intr['tab_title'], 'tab_title')
        self.assertEqual(config._intr['tab_condition'], 'tab_condition')
        self.assertEqual(config._intr['check_csrf'], True)
        self.assertEqual(config._intr['csrf_token'], 'csrf_token')

class Test_mgmt_path(unittest.TestCase):
    def _makeOne(self, request):
        from .. import mgmt_path
        return mgmt_path(request)

    def test_it(self):
        from .. import MANAGE_ROUTE_NAME
        request = testing.DummyRequest()
        context = testing.DummyResource()
        def route_path(route_name, *arg, **kw):
            self.assertEqual(route_name, MANAGE_ROUTE_NAME)
            self.assertEqual(arg, ('a',))
            self.assertEqual(kw, {'b':1, 'traverse':('',)})
            return '/path'
        request.route_path = route_path
        inst = self._makeOne(request)
        result = inst(context, 'a', b=1)
        self.assertEqual(result, '/path')


class Test__default(unittest.TestCase):
    def _makeOne(self):
        from .. import _default
        return _default()

    def test__nonzero__(self):
        self.assertFalse(self._makeOne())

    def test___repr__(self):
        inst = self._makeOne()
        self.assertEqual(repr(inst), '(default)')
        
class Test_mgmt_view(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import mgmt_view
        return mgmt_view

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_create_defaults(self):
        decorator = self._makeOne()
        self.assertEqual(decorator.__dict__, {})

    def test_create_context_trumps_for(self):
        decorator = self._makeOne(context='123', for_='456')
        self.assertEqual(decorator.context, '123')

    def test_create_for_trumps_context_None(self):
        decorator = self._makeOne(context=None, for_='456')
        self.assertEqual(decorator.context, '456')

    def test_create_nondefaults(self):
        decorator = self._makeOne(
            name=None, request_type=None, for_=None,
            permission='foo', mapper='mapper',
            decorator='decorator', match_param='match_param'
            )
        self.assertEqual(decorator.name, None)
        self.assertEqual(decorator.request_type, None)
        self.assertEqual(decorator.context, None)
        self.assertEqual(decorator.permission, 'foo')
        self.assertEqual(decorator.mapper, 'mapper')
        self.assertEqual(decorator.decorator, 'decorator')
        self.assertEqual(decorator.match_param, 'match_param')
        
    def test_call_function(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, 'abc')
        self.assertEqual(context.config.view, 'abc')

    def test_call_class_no_attr(self):
        decorator = self._makeOne()
        info = DummyVenusianInfo(scope='class')
        venusian = DummyVenusian(info)
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, None)
        self.assertEqual(context.config.settings['attr'], 'foo')

    def test_call_class_with_attr(self):
        decorator = self._makeOne(attr='bar')
        info = DummyVenusianInfo(scope='class')
        venusian = DummyVenusian(info)
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, None)
        self.assertEqual(context.config.settings['attr'], 'bar')

class Test_get_mgmt_views(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, request, context=None, names=None):
        from .. import get_mgmt_views
        return get_mgmt_views(request, context, names)

    def test_no_views_found(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.registry.introspector = DummyIntrospector()
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_no_related_view(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_gardenpath(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [{'view_name': 'name', 'tab_title': 'Name'}])

    def test_one_related_view_somecontext_tabcondition_None(self):
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = IFoo
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_instcontext_tabcondition_None(self):
        class Foo(object):
            pass
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = Foo
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_False(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = False
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_callable(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        def tabcondition(context, request):
            return False
        intr['tab_title'] = None
        intr['tab_condition'] = tabcondition
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_not_in_names(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request, names=('fred',))
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_predicatefail(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        class Thing(object):
            def __predicated__(self, context, request):
                return False
        thing = Thing()
        view_intr['derived_callable'] = thing
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_permissionfail(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        class Thing(object):
            def __permitted__(self, context, request):
                return False
        thing = Thing()
        view_intr['derived_callable'] = thing
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector((intr,))
        result = self._callFUT(request)
        self.assertEqual(result, [])

    def test_one_related_view_gardenpath_tab_title_sorting(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'b'
        intr['tab_condition'] = None
        intr2 = {}
        intr2['tab_title'] = 'a'
        intr2['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        intr2 = DummyIntrospectable(related=(view_intr,), introspectable=intr2)
        request.registry.introspector = DummyIntrospector((intr, intr2))
        result = self._callFUT(request)
        self.assertEqual(result,
                         [{'view_name': 'name', 'tab_title': 'a'},
                          {'view_name': 'name', 'tab_title': 'b'}])

    def test_one_related_view_gardenpath_with_taborder(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda *arg: '/path'
        request.registry.content = DummyContent(('b',))
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'b'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        view_intr2 = DummyIntrospectable()
        view_intr2.category_name = 'views'
        view_intr2['name'] = 'a'
        view_intr2['context'] = None
        view_intr2['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'b'
        intr['tab_condition'] = None
        intr2 = {}
        intr2['tab_title'] = 'a'
        intr2['tab_condition'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        intr2 = DummyIntrospectable(related=(view_intr2,), introspectable=intr2)
        request.registry.introspector = DummyIntrospector((intr, intr2))
        result = self._callFUT(request)
        self.assertEqual(result,
                         [{'view_name': 'b', 'tab_title': 'b'},
                          {'view_name': 'a', 'tab_title': 'a'}])

class DummyContent(object):
    def __init__(self, result=None):
        self.result = result
        
    def metadata(self, *arg, **kw):
        return self.result

class DummyIntrospector(object):
    def __init__(self, result=()):
        self.result = result
        
    def get_category(self, *arg):
        return self.result

class DummyVenusianInfo(object):
    scope = None
    codeinfo = None
    module = None
    def __init__(self, **kw):
        self.__dict__.update(kw)
    
class DummyVenusian(object):
    def __init__(self, info=None):
        if info is None:
            info = DummyVenusianInfo()
        self.info = info
        
    def attach(self, wrapped, callback, category):
        self.wrapped = wrapped
        self.callback = callback
        self.category = category
        return self.info

class DummyConfigurator(object):
    _ainfo = None
    def __init__(self):
        self._intr = DummyIntrospectable()
        self._actions = []
        self._added = None

    def object_description(self, ob):
        return ob
        
    def maybe_dotted(self, thing):
        return thing

    def add_view(self, **kw):
        self._added = kw

    def add_mgmt_view(self, view=None, **settings):
        self.view = view
        self.settings = settings

    def with_package(self, other):
        return self

    def introspectable(self, category, discrim, desc, name):
        self.desc = desc
        return self._intr

    def action(self, discriminator, introspectables):
        self._actions.append((discriminator, introspectables))
    
class DummyIntrospectable(dict):
    def __init__(self, **kw):
        dict.__init__(self, **kw)
        self.related = {}
        
    def relate(self, category, discrim):
        self.related[category] = discrim
        