from Scientific.Physics.PhysicalQuantities import PhysicalQuantity as PQ
from collections import OrderedDict
import re, inspect, numpy
from math import *  # enable eval to work with math functions

class DataItem:
    """
    Represent a data item (parameter) by its name, a default value,
    and an optional set of attributes that describe the data item.
    Typical attributes are

    ============== ==================================================
    Name           Description
    ============== ==================================================
    ``name``       name (mandatory)
    ``default``    default value
    ``unit``       registered unit
    ``help``       description of the data item
    ``str2type``   object transforming a string to desired type,
                   can be ``eval``, ``float``, ... Based on type
                   of ``default`` if not given.
    ``value``      current value assigned in a user interface
    ``minmax``     legal interval (2-list) of values
    ``options``    legal list of values
    ``widget``     recommended widget in graphical user interfaces
    ``namespace``  user's namespace for use when ``str2type=eval``
    ``user_data``  meta data stored in this object
    ``validate``   callable that can validate the value
    ``symbol``     LaTex code for mathematical symbol
    ============== ==================================================

    A number and a unit can be
    """
    _legal_data = 'name default unit help value str2type minmax options widget validator namespace user_data symbol'.split()

    def _signature(self):
        """Return output signature with "DataItem: name=..."."""
        return 'DataItem "%s"' % self.name

    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise ValueError('DataItem: name must be an argument')
        self.name = kwargs['name']

        if 'default' not in kwargs:
            kwargs['default'] = None  # indicates required variable

        # Check that all arguments are valid
        for arg in kwargs:
            if arg not in self._legal_data:
                raise ValueError(
                    '%s argument %s=%s is not valid. Valid '
                    'arguments are\n%s' %
                    (self._signature(), arg, kwargs[arg],
                     ', '.join(self._legal_data)))

        self.data = OrderedDict(**kwargs)

        if 'str2type' not in self.data:
            # use type(default) as str2type, except for
            # boolean values
            if self.data['default'] is None:
                self.data['str2type'] = str
            elif isinstance(self.data['default'], basestring):
                self.data['str2type'] = str
            elif type(self.data['default']) == type(True):
                self.data['str2type'] = str2bool
            elif type(self.data['default']) in (
                type(()), type([]), type({})):
                self.data['str2type'] = eval
            elif isinstance(self.data['default'], numpy.ndarray):
                self.data['str2type'] = lambda s: numpy.asarray(eval(s))
            elif type(self.data['default']) in (
                type(2.0), type(2), type(2+0j)):
                self.data['str2type'] = type(self.data['default'])
            else:
                # Assume user's non-standard data can be turned
                # from str to object via eval and self.data['namespace']
                self.data['str2type'] = eval

        self._check_validity_of_data()

        self._values = [self.data['default']]
        self._assigned_value = False  # True if value from UI

    def _check_validity_of_data(self):
        if 'minmax' in self.data:
            attr = self.data['minmax']
            if not isinstance(attr, (list,tuple)):
                raise TypeError(
                    '%s: minmax must be 2-list/tuple, not %s' %
                    self._signature(), type(attr))
            if len(attr) != 2:
                raise TypeError(
                    '%s: minmax list/tuple must have length 2, not %d' %
                    self._signature(), len(attr))
            if not isinstance(attr[0], (float,int)) or \
               not isinstance(attr[1], (float,int)):
                ValueError('%s: minmax has wrong data types [%s, %s]' %
                           self._signature(),
                           type(attr[0]), type(attr[1]))

        if 'options' in self.data:
            attr = self.data['options']
            if not isinstance(attr, (list,tuple)):
                raise TypeError(
                    '%s: options must list/tuple, not %s' %
                    type(attr))

        for attr in 'help', 'widget':
            if attr in self.data:
                if not isinstance(self.data[attr], basestring):
                    raise TypeError('%s: %s must be string, not %s' %
                                    self._signature(), attr,
                                    type(self.data[attr]))

    def _process_value(self, value):
        """
        Perform unit conversion (if relevant), convert to string
        value to right type according to str2type, and perform
        validation.
        """
        value = self._handle_unit_conversion(value)

        # Convert value to the right type

        if not 'str2type' in self.data:
            return value
        if inspect.isclass(self.data['str2type']) and \
               issubclass(self.data['str2type'], basestring):
            return value

        # Otherwise, convert to registered type (str2type)
        if self.data['str2type'] == eval:
            # Execute in some namespace?
            if 'namespace' in self.data:
                value = eval(value, self.data['namespace'])
            else:
                try:
                    value = eval(value)
                    # Note: this eval can handle math expressions
                    # like sin(pi/2) since this module imports all of
                    # the math module
                except:
                    # value is a string
                    pass
        else:
            try:
                value = self.data['str2type'](value)
            except Exception, e:
                raise TypeError(
                'could not apply str2type=%s to value %s %s\n'\
                'Python exception: %s' %
                (self.data['str2type'], value, type(value), e))

        return value

    def _validate(self, value):
        if 'minmax' in self.data:
            lo, hi = self.data['minmax']
            if not (lo <= value <= hi):
                raise DataItmValueError(
                    '%s: value=%s not in [%s, %s]' %
                    self._signature(), value, lo, hi)

        if 'options' in self.data:
            if value not in self.data['options']:
                raise DataItemValueError(
                    '%s: wrong value=%s not in %s' %
                    (self._signature(), value, self.data['options']))

    def _handle_unit_conversion(self, value):
        """
        Return converted value (float) if value with unit,
        otherwise just return value.
        """
        # Is value a number and a unit?
        number_with_unit = r'^\s*([Ee.0-9+-]+) +([A-Za-z0-9*/]+)\s*$'
        if re.search(number_with_unit, value):
            q = PQ(value)  # quantity with unit
            if 'unit' in self.data:
                registered_unit = self.data['unit']
                if registered_unit != q.getUnitName():
                    if q.isCompatible(registered_unit):
                        q.convertToUnit(registered_unit)
                    else:
                        raise DataItemValueError(
                            '%s: value=%s, unit %s is not compatible with '
                            'registered unit %s' %
                            (self._signature(), value, q.getUnitName(),
                            registered_unit))
            else:
                # No unit registered, register this one
                self.data['unit'] = unit
            value = q.getValue()  # always float
        # else: just return value as it came in
        return value              # float if with unit, otherwise str

    def get(self, attribute_name):
        """Return value of attribute name."""
        if attribute_name in self.data:
            return self.data[attribute_name]
        else:
            raise ValueError(
                '%s: no attribute with name "%s"\n'
                'registered names are %s' %
                (self._signature(), attribute_name,
                 ', '.join(list(self.data.keys()))))

    def set_value(self, value):
        """Set value as a string."""
        if not isinstance(value, str):
            raise ValueError('%s: value=%s %s must be a string' %
                             (self._signature(), value, type(value)))
        # The item can have a single value or multiple values
        if '&' in value:
            self._values = [v.strip() for v in value.split('&')]
        else:
            self._values = [value]

        validate = self.data.get('validate', DataItem._validate)
        for i in range(len(self._values)):
            value = self._process_value(self._values[i])
            validate(self, value)
            self._values[i] = value

        self._assigned_value = True

    def get_values(self):
        """Return (possibly multiple) values set for this data item."""
        if self._values == [None]:
            pass
            #raise ValueError(
            #    '%s: value not set.\ndefault=None so value must be set.' %
            #    self._signature())
        return self._values

    def get_value(self, with_unit=False, fmt=None):
        """
        Return a single value set for this data item.
        with_unit returns the value and the unit as a string, and
        in that case fmt can be used to specify the formatting.
        Without fmt the registered value is returned, with fmt
        given, the value is returned as a string formatted according
        to fmt.
        """
        if fmt:
            value = fmt % self.get_values()[0]
        else:
            value = '%s' % self.get_values()[0]

        if with_unit:
            if 'unit' in self.data:
                return '%s %s' % (value, self.data['unit'])
            else:
                return '%s (no unit)' % value
        else:
            if fmt:
                return value
            else:
                return self.get_values()[0]

    def has_multiple_values(self):
        return len(self._values) > 1

    def __str__(self):
        """Return pretty print of this data item."""
        attribute_names = list(self.data.keys())
        attribute_names.remove('name')
        import pprint
        s = '%s:' % self._signature()
        if self.has_multiple_values():
            s += ' multiple values: %s' % self.get_values()
        else:
            s += ' value=%s' % self.get_value()

        s += ' ' + ', '.join(['%s=%s' % (name, self.data[name])
                       for name in sorted(attribute_names)])
        return s

    def __repr__(self):
        args = ', '.join(['%s=%s' % (attr, repr(self.data[attr]))
                          for attr in self.data])
        return '%s(%s)' % (self.__class__.__name__, args)

def str2bool(s):
    """
    Turn a string s, holding some boolean value
    ('on', 'off', 'True', 'False', 'yes', 'no' - case insensitive)
    into boolean variable. s can also be a boolean. Example:

    >>> str2bool('OFF')
    False
    >>> str2bool('yes')
    True
    """
    if isinstance(s, str):
        true_values = ('on', 'true', 'yes')
        false_values = ('off', 'false', 'no')
        s2 = s.lower()  # make case insensitive comparison
        if s2 in true_values:
            return True
        elif s2 in false_values:
            return False
        else:
            raise ValueError('"%s" is not a boolean value %s' % \
                             (s, true_values+false_values))
    else:
        raise TypeError('%s %s (not string!) cannot be converted to bool' % \
                        (s, type(s)))


class DataItemValueError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    __repr__ = __str__


import nose.tools as nt

def test_DataItem_set_value():
    d = DataItem(name='A', default=1.0)  # minimal
    print isinstance(d, Leaf), issubclass(DataItem, Leaf) #[[[

    # Test that non-strings cannot be assigned with set_value
    try:
        d.set_value(2)
        assert False, 'should be illegal to set a value that is not a string'
    except ValueError:
        pass
    try:
        d.set_value('some method')
        assert False, 'should be illegal to convert "some method" to str2type=float'
    except TypeError:
        pass

    # Test that plain assignment works: value and type
    d.set_value('2')
    nt.assert_equal(d.get_value(), 2.0)
    nt.assert_equal(type(d.get_value()), d.data['str2type'])

def test_DataItem_required_value():
    # A required variable is indicated by missing default or
    # default set to None

    d = DataItem(name='A')  # no default, must set variable, type str

    nt.assert_equal(d.get_value(), None)
    # Test that non-strings cannot be assigned with set_value
    try:
        d.set_value(2)
        assert False, 'cannot set value to 2 - must be a string'
    except:
        pass
    whatever = 'just something'
    d.set_value(whatever)
    nt.assert_equal(d.get_value(), whatever)
    nt.assert_equal(type(d.get_value()), d.data['str2type'])

def test_DataItem_unit_conversion():
    d = DataItem(name='V', default=0.2, help='velocity', unit='m/s')
    nt.assert_equal(d.get_values(), [0.2])
    d.set_value('2 km/h')
    nt.assert_equal(d.get_value(with_unit=True,
                                 fmt='%5.2f').strip(),
                    '0.56 m/s')
    nt.assert_almost_equal(d.get_value(), 0.555555555, places=6)

    try:
        d.set_value('5.2 kg/m')
        assert False, 'wrong unit should trigger exception'
    except:
        pass


def test_DataItem_str2type():
    # Test assignments with str2type=eval
    d = DataItem(name='U', default=2, str2type=eval)
    values_str = ['[1, 2, 3, 4]', 'some method', '2.3']
    values = [[1, 2, 3, 4], 'some method', 2.3]
    for value_str, value in zip(values_str, values):
        d.set_value(value_str)
        nt.assert_equal(d.get_value(), value)

    # Test user-defined function for str2type: str to numpy array
    # via list syntax
    def str2d(s):
        return numpy.asarray(eval(s), dtype=numpy.float)

    d = DataItem(name='Q', default=1.5, str2type=str2d)
    nt.assert_equal(d.get_value(), 1.5)
    d.set_value('[-1, 5, 8]')
    diff = numpy.abs(d.get_value() - numpy.array([-1, 5, 8.])).max()
    nt.assert_almost_equal(diff, 0, places=14)

    # Test class for str2type
    class Str2d:
        def __call__(self, s):
            return int(round(float(s)))

    d = DataItem(name='T', default=2, str2type=Str2d())
    d.set_value('3.87')
    nt.assert_equal(d.get_value(), 4)

def test_DataItem_validate():
    # Should do checking for values in DataItem and also call validator
    legal_values = 'Newton Secant Bisection'.split()
    d = DataItem(name='method', default='Newton',
                 options=legal_values)
    try:
        d.set_value('Broyden')
        assert False, 'wrong value, not among options'
    except:
        pass
    d.set_value('Secant')
    nt.assert_equal(d.get_value(), 'Secant')

    # User-supplied validation function, here case-insensitive
    # test of some options
    class Validate:
        def __init__(self, legal_values):
            self.legal_values = [v.lower() for v in legal_values]

        def __call__(self, data_item, value):
            if value.lower() not in self.legal_values:
                raise DataItemValueError(
                    '%s: %s not in %s' %
                    (data_item._signature(), value, self.legal_values))

    validate = Validate(legal_values)
    d = DataItem(validate=validate, **d.data)
    d.set_value('NEWTON')
    nt.assert_equal(d.get_value(), 'NEWTON')

def test_DataItem_multiple_values():
    legal_values = 'Newton Secant Bisection'.split()
    d = DataItem(name='method', default='Secant',
                 options=legal_values)
    values = 'Newton & Secant & Bisection'
    d.set_value(values)
    nt.assert_equal(d.get_values(), values.split(' & '))

    d = DataItem(name="a", help="piecewise constant function values",
                 default=[1])
    values = '[1, 5, 0.1]   & [10, 1, 100, 1000] & [4] &[9, 2.5]'
    d.set_value(values)
    expected = [eval(a) for a in values.split('&')]
    nt.assert_equal(d.get_values(), expected)

def test_DataItem_str():
    """Test output of __str__."""
    d = DataItem(name='Q', default=1.2, minmax=[0,2],
                 widget='slider', help='volume flux')
    answer = """DataItem "Q": value=1.2 default=1.2, help=volume flux, minmax=[0, 2], str2type=<type 'float'>, widget=slider"""
    nt.assert_equal(str(d), answer)

def test_DataItem_math():
    # Test use of basic functions from math (available in DataItem)
    d = DataItem(name='q', default=0, str2type=eval)
    d.set_value('sin(pi/2)*exp(0) & pi**2')
    nt.assert_almost_equal(d.get_values()[0], 1, places=14)
    nt.assert_almost_equal(d.get_values()[1], pi**2, places=14)

def test_DataItem_namespace():
    # Define user-specific function and use that when setting values
    # (eval in DataItem will use local namespace)
    def Gaussian(x, mean=0, sigma=1):
        return 1/(sqrt(2*pi)*sigma)*exp(-(x-mean)**2/(2*sigma**2))

    d = DataItem(name='q', default=0, namespace=locals(), str2type=eval)
    d.set_value('Gaussian(2, 2, 3) & Gaussian(3)')
    nt.assert_almost_equal(d.get_values()[0], 0.1329807601338109, places=12)
    nt.assert_almost_equal(d.get_values()[1], 0.0026880519410391462, places=12)

def test_DataItem_dict2DataItem():
    data = dict(name="A", help="area", default=1, str2type=float)
    d = DataItem(**data)
    nt.assert_equal(str(d), """DataItem "A": value=1 default=1, help=area, str2type=<type 'float'>""")


if __name__ == '__main__':
    test_DataItem_set_value()
    test_DataItem_required_value()
    test_DataItem_unit_conversion()
    test_DataItem_str2type()
    test_DataItem_validate()
    test_DataItem_multiple_values()
    test_DataItem_str()
    test_DataItem_math()
    test_DataItem_namespace()
    test_DataItem_dict2DataItem()
