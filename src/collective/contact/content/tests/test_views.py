# -*- coding: utf8 -*-
import unittest2 as unittest

from collective.contact.content.testing import INTEGRATION


ADDRESS_FIELDS = ['country', 'region', 'zip_code',
                  'city', 'street', 'number',
                  'additional_address_details']


class TestView(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        super(TestView, self).setUp()
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        mydirectory = self.portal['mydirectory']
        self.degaulle = mydirectory['degaulle']
        self.adt = self.degaulle['adt']
        self.gadt = self.degaulle['gadt']
        self.pepper = mydirectory['pepper']
        self.sergent_pepper = self.pepper['sergent_pepper']
        self.rambo = mydirectory['rambo']
        self.armeedeterre = mydirectory['armeedeterre']
        self.corpsa = self.armeedeterre['corpsa']
        self.divisionalpha = self.corpsa['divisionalpha']
        self.regimenth = self.divisionalpha['regimenth']
        self.brigadelh = self.regimenth['brigadelh']
        self.general_adt = self.armeedeterre['general_adt']
        self.sergent_lh = self.brigadelh['sergent_lh']
        self.mydirectory = mydirectory


class TestAddressView(TestView):

    def test_degaulle_address_view(self):
        address_view = self.degaulle.restrictedTraverse("@@address")
        data = address_view.namespace()
        for field in ADDRESS_FIELDS:
            self.assertIn(field, data)
        self.assertEqual(data['country'], 'France')
        self.assertEqual(data['number'], '6bis')
        self.assertEqual(data['street'], 'rue Jean Moulin')
        self.assertEqual(data['city'], "Colombey les deux églises")
        self.assertEqual(data['zip_code'], '52330')
        self.assertEqual(data['region'], '')
        self.assertEqual(data['additional_address_details'], 'bâtiment D')

    def test_pepper_address_view(self):
        address_view = self.pepper.restrictedTraverse("@@address")
        data = address_view.namespace()
        for field in ADDRESS_FIELDS:
            self.assertIn(field, data)
        self.assertEqual(data['country'], 'England')
        self.assertEqual(data['city'], "Liverpool")

    def test_rambo_address_view(self):
        # no address information
        address_view = self.rambo.restrictedTraverse("@@address")
        data = address_view.namespace()
        for field in ADDRESS_FIELDS:
            self.assertIn(field, data)
            self.assertEqual(data[field], '')

    def test_regimenth_address_view(self):
        # an organization have an address view
        address_view = self.regimenth.restrictedTraverse("@@address")
        data = address_view.namespace()
        for field in ADDRESS_FIELDS:
            self.assertIn(field, data)
        self.assertEqual(data['number'], '11')
        self.assertEqual(data['street'], "rue de l'harmonie")
        self.assertEqual(data['city'], "Villeneuve d'Ascq")
        self.assertEqual(data['zip_code'], '59650')
        self.assertEqual(data['region'], '')
        self.assertEqual(data['additional_address_details'], '')
    # TODO: test that a position can have an address


class TestContactView(TestView):

    def test_contact_view(self):
        contact_view = self.gadt.restrictedTraverse("@@contact")
        contact_view.update()

        self.assertEqual(contact_view.fullname,
                         "Général Charles De Gaulle")
        self.assertEqual([self.armeedeterre],
                         contact_view.organizations)
        # address is acquired from degaulle
        address = contact_view.address
        self.assertEqual(address['number'], '6bis')
        self.assertEqual(address['street'], "rue Jean Moulin")
        self.assertEqual(address['city'], "Colombey les deux églises")
        self.assertEqual(address['zip_code'], '52330')
        self.assertEqual(address['region'], '')
        self.assertEqual(address['additional_address_details'], 'bâtiment D')

    def test_contact_details_acquisition(self):
        contact_view = self.sergent_pepper.restrictedTraverse("@@contact")
        contact_view.update()
        self.assertEqual(contact_view.fullname, "Sergent Pepper")
        self.assertEqual(self.sergent_lh,
                         contact_view.position)
        organizations = contact_view.organizations
        self.assertEqual([self.armeedeterre,
                          self.corpsa,
                          self.divisionalpha,
                          self.regimenth,
                          self.brigadelh], organizations)

        # Person email comes before Position email
        self.assertEqual(contact_view.email,
                         "sgt.pepper@armees.fr")
        self.assertNotEqual(contact_view.email,
                            "brigade_lh@armees.fr")
        self.assertEqual(contact_view.phone,
                         "0288552211")
        self.assertEqual(contact_view.cell_phone,
                         '0654875233')
        self.assertEqual(contact_view.im_handle,
                         "brigade_lh@jabber.org")

        # Everything in Sgt Pepper's address is acquired from Régiment H
        address = contact_view.address
        self.assertEqual(address['number'], '11')
        self.assertEqual(address['street'], "rue de l'harmonie")
        self.assertEqual(address['city'], "Villeneuve d'Ascq")
        self.assertEqual(address['zip_code'], '59650')
        self.assertEqual(address['region'], '')
        self.assertEqual(address['additional_address_details'], '')


class TestPositionView(TestView):

    def test_position_view(self):
        position_view = self.sergent_lh.restrictedTraverse("@@position")
        position_view.update()

        self.assertEqual(position_view.name, "Sergent de la brigade LH")
        self.assertEqual(position_view.type, "sergent")
        organizations = position_view.organizations
        self.assertEqual([self.armeedeterre,
                          self.corpsa,
                          self.divisionalpha,
                          self.regimenth,
                          self.brigadelh], organizations)

        self.assertEqual(position_view.email,
                         "brigade_lh@armees.fr")

        address = position_view.address
        self.assertEqual(address['number'], '11')
        self.assertEqual(address['street'], "rue de l'harmonie")
        self.assertEqual(address['city'], "Villeneuve d'Ascq")
        self.assertEqual(address['zip_code'], '59650')
        self.assertEqual(address['region'], '')
        self.assertEqual(address['additional_address_details'], '')