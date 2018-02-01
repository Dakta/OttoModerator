#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

class TestCriterion(unittest.TestCase):
    pass
class TestAction(unittest.TestCase):
    pass

class TestRule(unittest.TestCase):
    def setUp(self):
        pass

    def test_shuffle(self):
        # self.assertEqual(self.seq, range(10))
        # # should raise an exception for an immutable sequence
        # self.assertRaises(TypeError, random.shuffle, (1,2,3))
        # self.assertTrue(element in self.seq)

        # with self.assertRaises(ValueError):
        #     random.sample(self.seq, 20)
        # for element in random.sample(self.seq, 5):
        #     self.assertTrue(element in self.seq)


if __name__ == '__main__':
    unittest.main()