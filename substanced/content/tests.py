import sys
import unittest

from pyramid import testing

class TestContentRegistry(unittest.TestCase):
    def _makeOne(self):
        from . import ContentRegistry
        return ContentRegistry()

    def test_add(self):
        inst = self._makeOne()
        inst.add('ct', 'ft', None)
        self.assertEqual(inst.factory_types['ft'], 'ct')
        self.assertEqual(inst.content_types['ct'], None)
        self.assertEqual(inst.meta['ct'], {})

    def test_add_with_meta(self):
        inst = self._makeOne()
        inst.add('ct', 'ft', None, icon='fred')
        self.assertEqual(inst.content_types['ct'], None)
        self.assertEqual(inst.meta['ct'], {'icon':'fred'})
        
    def test_create(self):
        inst = self._makeOne()
        inst.content_types['dummy'] = lambda a: a
        self.assertEqual(inst.create('dummy', 'a'), 'a')

    def test_typeof(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__factory_type__ = 'dummy'
        inst.factory_types['dummy'] = 'ct'
        self.assertEqual(inst.typeof(dummy), 'ct')

    def test_typeof_ct_missing(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__factory_type__ = 'dummy'
        self.assertEqual(inst.typeof(dummy), None)

    def test_istype_true(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__factory_type__ = 'dummy'
        inst.factory_types['dummy'] = 'ct'
        self.assertTrue(inst.istype(dummy, 'ct'))

    def test_istype_false(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__factory_type__ = 'notdummy'
        inst.factory_types['dummy'] = 'ct'
        self.assertFalse(inst.istype(dummy, 'dummy'))

    def test_exists(self):
        inst = self._makeOne()
        inst.content_types['category'] = True
        self.assertTrue(inst.exists('category'))
        self.assertFalse(inst.exists('foobar'))
        
    def test_metadata(self):
        inst = self._makeOne()
        inst.factory_types['dummy'] = 'ct'
        inst.content_types['ct'] = True
        inst.meta['ct'] = {'icon':'icon-name'}
        dummy = Dummy()
        dummy.__factory_type__ = 'dummy'
        self.assertEqual(inst.metadata(dummy, 'icon'), 'icon-name')

    def test_metadata_notfound(self):
        inst = self._makeOne()
        inst.factory_types['dummy'] = 'ct'
        inst.content_types['ct'] = True
        inst.meta['dummy'] = {'icon':'icon-name'}
        dummy = Dummy()
        dummy.__factory_type__ = 'dummy'
        self.assertEqual(inst.metadata(dummy, 'doesntexist'), None)

    def test_all(self):
        inst = self._makeOne()
        inst.content_types['dummy'] = True
        inst.content_types['category'] = True
        self.assertEqual(sorted(inst.all()), ['category', 'dummy'])
        
class Test_content(unittest.TestCase):
    def _makeOne(self, content_type):
        from ..content import content
        return content(content_type)

    def test_decorates_class(self):
        decorator = self._makeOne('special')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        class Dummy(object):
            pass
        wrapped = decorator(Dummy)
        self.assertTrue(wrapped is Dummy)
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)

    def test_decorates_function(self):
        decorator = self._makeOne('special')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        def dummy(): pass
        wrapped = decorator(dummy)
        self.assertTrue(wrapped is dummy)
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)

class Test_add_content_type(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from . import add_content_type
        return add_content_type(*arg, **kw)

    def test_success_function(self):
        dummy = Dummy()
        def factory(): return dummy
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        self._callFUT(config, 'foo', factory, category=Dummy)
        self.assertEqual(len(config.actions), 2)
        ft = config.actions[0][0][0]
        self.assertEqual(
            ft,
            ('sd-factory-type', 'substanced.content.tests.factory')
            )
        self.assertEqual(
            config.actions[1][0][0],
            ('sd-content-type', 'foo')
            )
        config.actions[1][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], Dummy)
        self.assertEqual(
            config.registry.content.added[0][0][0], 'foo')
        self.assertEqual(
            config.registry.content.added[0][0][2](), dummy)

    def test_success_class(self):
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo, category=Dummy)
        self.assertEqual(len(config.actions), 2)
        ft = config.actions[0][0][0]
        self.assertEqual(
            ft,
            ('sd-factory-type', 'substanced.content.tests.Foo')
            )
        self.assertEqual(
            config.actions[1][0][0],
            ('sd-content-type', 'foo')
            )
        config.actions[1][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], Dummy)
        self.assertEqual(
            config.registry.content.added[0][0][0], 'foo')
        content = config.registry.content.added[0][0][2]()
        self.assertEqual(content.__class__, Foo)

    def test_with_extra_flag(self):
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo, catalog=True)
        self.assertEqual(len(config.actions), 2)
        meta = config.actions[1][1]['introspectables'][0]['meta']
        self.assertEqual(meta['catalog'], True)

class Test_wrap_factory(unittest.TestCase):
    def _callFUT(self, factory, factory_type):
        from . import wrap_factory
        return wrap_factory(factory, factory_type)

    def test_content_factory_isclass_factory_type_is_not_supplied(self):
        class Foo(object):
            pass
        factory_type, factory = self._callFUT(Foo, None)
        self.assertTrue(factory is Foo)
        self.assertEqual(factory_type, 'substanced.content.tests.Foo')

    def test_content_factory_isclass_factory_type_is_supplied(self):
        class Foo(object):
            pass
        factory_type, factory = self._callFUT(Foo, 'dummy')
        self.assertFalse(factory is Foo)
        self.assertEqual(factory_type, 'dummy')
        self.assertTrue(factory.__factory__ is Foo)
        ob = factory()
        self.assertTrue(ob.__class__ is Foo)
        self.assertEqual(ob.__factory_type__, 'dummy')

    def test_content_factory_isfunction_factory_type_not_supplied(self):
        class Foo(object):
            pass
        foo = Foo()
        def ctor():
            return foo
        factory_type, factory = self._callFUT(ctor, None)
        self.assertFalse(factory is ctor)
        self.assertTrue(factory.__factory__ is ctor)
        ob = factory()
        self.assertTrue(ob is foo)
        self.assertEqual(ob.__factory_type__, 'substanced.content.tests.ctor')

    def test_content_factory_isfunction_factory_type_is_supplied(self):
        class Foo(object):
            pass
        foo = Foo()
        def ctor():
            return foo
        factory_type, factory = self._callFUT(ctor, 'dummy')
        self.assertFalse(factory is ctor)
        self.assertTrue(factory.__factory__ is ctor)
        ob = factory()
        self.assertTrue(ob is foo)
        self.assertEqual(ob.__factory_type__, 'dummy')

class TestContentTypePredicate(unittest.TestCase):
    def _makeOne(self, val, config):
        from . import ContentTypePredicate
        return ContentTypePredicate(val, config)

    def _makeConfig(self, result):
        config = Dummy()
        config.registry = Dummy()
        config.registry.content = Dummy()
        config.registry.content.typeof = lambda *x: result
        return config
    
    def test___call___true(self):
        config = self._makeConfig('abc')
        inst = self._makeOne('abc', config)
        context = Dummy()
        result = inst(context, None)
        self.assertTrue(result)

    def test___call___false(self):
        config = self._makeConfig('notabc')
        inst = self._makeOne('abc', config)
        context = Dummy()
        result = inst(context, None)
        self.assertFalse(result)
        
    def test_text(self):
        config = self._makeConfig(True)
        inst = self._makeOne('abc', config)
        self.assertEqual(inst.text(), 'content_type = abc')

    def test_phash(self):
        config = self._makeConfig(True)
        inst = self._makeOne('abc', config)
        self.assertEqual(inst.phash(), 'content_type = abc')

class Test_get_content_type(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, registry=None):
        from . import get_content_type
        return get_content_type(resource, registry)

    def test_without_registry(self):
        self.config.registry.content = DummyContentRegistry()
        resource = Dummy()
        resource.type = 'foo'
        self.assertEqual(self._callFUT(resource), 'foo')
        
    def test_with_registry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        resource = Dummy()
        resource.type = 'bar'
        self.assertEqual(self._callFUT(resource, registry), 'bar')

class Test_get_factory_type(unittest.TestCase):
    def _callFUT(self, resource):
        from . import get_factory_type
        return get_factory_type(resource)

    def test_has_ft_attr(self):
        resource = Dummy()
        resource.__factory_type__ = 'abc'
        self.assertEqual(self._callFUT(resource), 'abc')

    def test_without_ft_attr(self):
        resource = Dummy()
        self.assertEqual(self._callFUT(resource),
                         'substanced.content.tests.Dummy')

class DummyContentRegistry(object):
    def __init__(self):
        self.added = []

    def add(self, *arg, **meta):
        self.added.append((arg, meta))

    def typeof(self, resource):
        return resource.type

class Dummy(object):
    pass

class DummyIntrospectable(dict):
    def __init__(self, *arg, **kw):
        pass

class DummyConfig(object):
    introspectable = DummyIntrospectable
    def __init__(self):
        self.registry = Dummy()
        self.actions = []
        self.content_types = []
    def action(self, *arg, **kw):
        self.actions.append((arg, kw))
    def with_package(self, module):
        return self
    def add_content_type(self, *arg, **kw):
        self.content_types.append((arg, kw))
        
class DummyVenusianContext(object):
    def __init__(self):
        self.config = DummyConfig()

def call_venusian(venusian, context=None):
    if context is None:
        context = DummyVenusianContext()
    for wrapped, callback, category in venusian.attachments:
        callback(context, None, None)
    return context.config
        
class DummyVenusianInfo(object):
    scope = 'notaclass'
    module = sys.modules['substanced.content.tests']
    codeinfo = 'codeinfo'

class DummyVenusian(object):
    def __init__(self, info=None):
        if info is None:
            info = DummyVenusianInfo()
        self.info = info
        self.attachments = []

    def attach(self, wrapped, callback, category=None):
        self.attachments.append((wrapped, callback, category))
        return self.info

