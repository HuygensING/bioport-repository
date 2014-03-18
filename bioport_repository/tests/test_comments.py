##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
# 
# This file is part of bioport.
# 
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

from datetime import datetime

from bioport_repository.tests.common_testcase import CommonTestCase, unittest 
from bioport_repository.person import Person


class CommentTestCase(CommonTestCase):

    def test_comment_creation_and_listing(self):
        p1 = Person('1234', repository=self.repo)
        comments = p1.get_comments()
        self.assertEqual(comments.count(), 0)
        comment_text = "This bio is really accurate!"
        p1.add_comment(text=comment_text)
        comments = p1.get_comments()
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments[0].text, comment_text)
        self.assertEqual(comments[0].created.toordinal(), datetime.now().toordinal())
        self.assertEqual(comments[0].submitter, 'Anonymous')
        p1.add_comment(text=comment_text + ' is not true!')


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [CommentTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite 

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
