# -*- coding: utf-8 -*-
"""
    test_datastore
    ~~~~~~~~~~~~~~

    REST Datastore tests
"""

from pytest import fixture

from rest_datastore import RESTUserDatastore


@fixture()
def datastore(request, app, tmpdir):
    return RESTUserDatastore()
