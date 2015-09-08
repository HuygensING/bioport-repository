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

import datetime


class BioPortException(Exception):
    pass


class BioPortNotFoundError(Exception):
    pass


def to_date(s, round='down'):  # @ReservedAssignment
    """Take a string in YYYY[-MM[-DD] format and return a date object

    round:
        one of ['down', 'up']: if 'down', take the lowest date, of 'up', take the max
        (i.e. to_date('2000', 'up') == datetime.datetime(2000, 1, 1))


    """
    if not s:
        return s
    if len(s) == 4:
        frmt = '%Y'
        result = datetime.datetime.strptime(s, frmt)
        if round == 'up':
            result = result.replace(month=12, day=31)
    elif len(s) == 7:
        frmt = '%Y-%m'
        result = datetime.datetime.strptime(s, frmt)
        if round == 'up':
            if result.month == 12:
                result = result.replace(month=1, year=result.year + 1)
                result = result - datetime.timedelta(1)
            else:
                result = result.replace(month=result.month + 1)
                result = result - datetime.timedelta(1)
    elif len(s) == 10:
        frmt = '%Y-%m-%d'
        result = datetime.datetime.strptime(s, frmt)
    else:
        raise ValueError('This data is not in ISO date format:%s' % s)

    return result


def format_date(d):
    """take a datetime instance, return a string

    (use this because strftime does not like dates before 1900)"""
    if d:
        return u"%04d-%02d-%02d %02d:%02d" % (d.year, d.month, d.day, d.hour, d.minute)
