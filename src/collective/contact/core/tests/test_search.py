# -*- coding: utf8 -*-

import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from ecreall.helpers.testing.base import BaseTest

from collective.contact.core.testing import INTEGRATION
from collective.contact.core.indexers import (
    held_position_searchable_text, organization_searchable_text,
    person_sortable_title, held_position_sortable_title)


class TestSearch(unittest.TestCase, BaseTest):
    """Tests search"""

    layer = INTEGRATION

    def setUp(self):
        super(TestSearch, self).setUp()
        self.portal = self.layer['portal']
        self.mydirectory = self.portal['mydirectory']
        self.degaulle = self.mydirectory['degaulle']
        self.pepper = self.mydirectory['pepper']
        self.armeedeterre = self.mydirectory['armeedeterre']
        self.general_adt = self.armeedeterre['general_adt']
        self.corpsa = self.armeedeterre['corpsa']
        self.corpsb = self.armeedeterre['corpsb']
        self.divisionalpha = self.corpsa['divisionalpha']
        self.divisionbeta = self.corpsa['divisionbeta']
        self.regimenth = self.divisionalpha['regimenth']
        self.brigadelh = self.regimenth['brigadelh']
        self.gadt = self.degaulle['gadt']
        self.sergent_pepper = self.pepper['sergent_pepper']

    def test_indexers(self):
        divisionalpha = self.divisionalpha
        self.assertEqual(organization_searchable_text(divisionalpha)(),
                         u"Armée de terre Corps A Division Alpha")
        gadt = self.gadt
        self.assertEqual(held_position_searchable_text(gadt)(),
                         u"Général Charles De Gaulle Général de l'armée de terre Armée de terre Émissaire OTAN")
        sergent_pepper = self.sergent_pepper
        self.assertEqual(held_position_searchable_text(sergent_pepper)(),
                         u"Sergent Pepper Sergent de la brigade LH Armée de terre Corps A Division Alpha Régiment H Brigade LH")
        pepper = self.pepper
        self.assertEqual(person_sortable_title(pepper)(),
                         "pepper")
        idxr = held_position_sortable_title(self.sergent_pepper)
        self.assertEqual(idxr(),
                         "pepper-sergent-de-la-brigade-lh-brigade-lh-armee-de-terre")
        degaulle = self.degaulle
        self.assertEqual(person_sortable_title(degaulle)(),
                         'de-gaulle-charles')

    def test_searchable_fields(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        results = catalog.searchResults(SearchableText='Gaulle')
        self.assertEqual(len(results), 3)
        results = catalog.searchResults(SearchableText='Général')
        self.assertEqual(len(results), 4)
        results = catalog.searchResults(SearchableText='Corps')
        self.assertEqual(len(results), 10)
        results_objects = [res.getObject() for res in results]
        self.assertIn(self.corpsa, results_objects)
        self.assertIn(self.corpsb, results_objects)
        self.assertIn(self.divisionalpha, results_objects)
        self.assertIn(self.divisionbeta, results_objects)
        self.assertIn(self.regimenth, results_objects)
        self.assertIn(self.brigadelh, results_objects)
        self.assertIn(self.sergent_pepper, results_objects)
        results = catalog.searchResults(SearchableText='armée')
        self.assertEqual(len(results), 15)
        results = catalog.searchResults(SearchableText='beta')
        self.assertEqual(len(results), 1)
        results = catalog.searchResults(SearchableText='régiment')
        self.assertEqual(len(results), 4)
        results = catalog.searchResults(SearchableText='brigade')
        self.assertEqual(len(results), 4)
        results = catalog.searchResults(SearchableText='Émissaire')
        self.assertEqual(len(results), 2)
