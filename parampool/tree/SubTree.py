
class SubTree:
    """
    Representation of a submenu as a list of leaf
    and SubTree objects.
    """
    def __init__(self, name, parent=None, level=0):
        self.name = name
        self.tree = []        # list of SubTree or Leaf objects
        self.parent = parent  # parent tree (like .. in a directory)

    def add(self, item):
        """Add a DataItem or SubTree object to this menu."""
        assert (isinstance(item, SubTree) or hasattr(item, 'name')), \
               item.__class__.__name__
        self.tree.append(item)

    def get_parent(self):
        if self.parent is None:
            raise ValueError(
                '%s is root so parent is non-existing' %
                self.name)
        return self.parent

    def __iter__(self):
        for item in self.tree:
            yield item

    def __str__(self):
        s = []
        for item in self.tree:
            s.append('%s "%s"' % (item.__class__.__name__, item.name))
        return '[' + ', '.join(s) + ']'

import nose.tools as nt

def test_SubTree():
    from DataItem import DataItem
    m1 = SubTree('main')
    d = DataItem(name='A', default=1)
    print dir(d)
    print isinstance(d, Leaf), issubclass(DataItem, Leaf)
    m1.add(DataItem(name='A', default=1))
    m1.add(DataItem(name='B', default=2))
    m2 = SubTree('sub1', parent=m1)
    m2.add(DataItem(name='C', default=3))
    m1.add(m2)
    nt.assert_equal(str(m1), '[DataItem "A", DataItem "B", SubTree "sub1"]')
    nt.assert_equal(str(m2), '[DataItem "C"]')
    nt.assert_equal(m2.get_parent(), m1)
    item_names = [m.name for m in m1]
    nt.assert_equal(item_names,['A', 'B', 'sub1'])

if __name__ == '__main__':
    test_SubTree()
