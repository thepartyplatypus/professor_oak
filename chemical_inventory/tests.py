import datetime
import json
import os
import time

from django.test import TestCase, RequestFactory, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from . import models

class ElementSearchTest(TestCase):
    """Filtering a list of chemicals by symbols in the formula."""

    fixtures = ['cabana_users.json', 'inventory_test_data.json']
    def test_included_elements(self):
        c = Client()
        response = c.get(
            reverse('element_search'),
            {'required':['Li']}
        )
        chemicals = response.context['chemicals']
        lithium = models.Chemical.objects.get(formula='Li')
        self.assertEqual(len(chemicals), 1)
        self.assertEqual(chemicals[0], lithium)

    def test_excluded_elements(self):
        c = Client()
        response = c.get(
            reverse('element_search'),
            {'excluded':['Li']}
        )
        chemicals = response.context['chemicals']
        self.assertFalse("Li" in [c.formula for c in chemicals])

    def test_two_letter_elements(self):
        """Make sure eg. searching H doesn't return He."""
        c = Client()
        response = c.get(
            reverse('element_search'),
            {'required':['H']}
        )
        chemicals = response.context['chemicals']
        self.assertTrue(len(chemicals) > 0)
        self.assertFalse('He' in [chemical.formula for chemical in chemicals])


class ChemicalTest(TestCase):
    """Unit tests for the Chemical class."""

    def setUp(self):
        self.chemical = models.Chemical()

    def test_is_in_stock(self):
        self.assertFalse(self.chemical.is_in_stock())


class ContainerAPITest(TestCase):
    fixtures = ['cabana_users.json', 'inventory_test_data.json']
    def setUp(self):
        # Create a dummy user
        self.user = User.objects.create_user('john',
                                             'john.lennon@example.com',
                                             'secret')
        self.client.login(username='john', password='secret')

    def test_auto_owner(self):
        """Make sure that creating a new chemical automatically sets the owner."""
        response = self.client.post(
            '/chemical_inventory/api/containers/',
            {'chemical': 1,
             'location': 1,
             'container_type': 'glass',
             'expiration_date': '2015-01-01',
             'state': 'powder'},
        )
        data = json.loads(response.content.decode())
        # Verify the object was created
        self.assertEqual(
            response.status_code,
            201
        )
        # Verify that `owner` was set
        savedContainer = models.Container.objects.get(pk=data['id'])
        self.assertEqual(
            savedContainer.owner,
            self.user
        )

    def test_iso_datestrings(self):
        """Javascript passes all dates with a time component. Does the
        serializer properly strip this time part."""
        # Make sure it only fixes it if the field is changed
        response = self.client.post(
            '/chemical_inventory/api/containers/',
            {'is_empty': True}
        )
        response = self.client.post(
            '/chemical_inventory/api/containers/',
            {'date_opened': '2015-09-21T19:39:41Z',
             'expiration_date': '2015-09-21T19:39:41Z'}
        )
        # List of errors should not contain anything for date_opened
        self.assertNotContains(response, 'date_opened', status_code=400)
        self.assertNotContains(response, 'expiration_date', status_code=400)


class SearchFormulaTest(TestCase):

    def test_autosave(TestCase):
        """Tests for saving data before strip"""
        chemical = models.Chemical(formula='CoF_2', health='0', flammability='0', instability='0', name='Cobalt(II) Fluoride')
        chemical.save()
        cobalt = models.Chemical.objects.get(formula='CoF_2')
        assert cobalt.stripped_formula == 'CoF2'
        
class IsEmptyTest(TestCase):
    '''Test for verifying whether a chemical as an expired but non-empty container'''
    fixtures = ['production_data']
    def test_not_empty_expired(TestCase):
        for chemicals in models.Chemical.objects.all():
            container_test = models.Container.objects.filter(chemical__id=chemicals.pk, expiration_date__lte=datetime.date.today(), is_empty=False).count()
            # print (container_test)
            assert type(container_test) is int


class OldDatabaseTest(TestCase):
    """Tests for importing the old database."""
    fixtures = ['inventory_test_data', 'cabana_users']
    chemicalfile = 'chemical_inventory/old-test-chemicals.csv'
    containerfile = 'chemical_inventory/old-test-containers.csv'
    def setUp(self):
        self.convert_chemicals = models.import_chemicals_csv
        self.convert_containers = models.import_containers_csv
        self.nitrile_glove = models.Glove.objects.get(name='Nitrile')

    def test_convert_chemicals(self):
        # Clear out chemicals loaded by fixture
        models.Chemical.objects.all().delete()
        assert models.Chemical.objects.count() == 0
        # Load new chemicals
        self.convert_chemicals(self.chemicalfile,
                               sds_dir='chemical_inventory/sds_test/')

        # Check first imported material
        lithium = models.Chemical.objects.get(name='Lithium')
        self.assertEqual(lithium.cas_number, '7439-93-2')
        self.assertEqual(lithium.name, 'Lithium')
        self.assertEqual(lithium.formula, 'Li')
        self.assertEqual(lithium.health, 3)
        # Default glove is set?
        self.assertIn(self.nitrile_glove, lithium.gloves.all())
        # Check for imported safety datasheet
        self.assertTrue(
            lithium.safety_data_sheet)
        os.remove(lithium.safety_data_sheet.path)
        # Other gloves set
        castor_oil = models.Chemical.objects.get(pk=12)
        assert castor_oil.name == 'Castor Oil'
        latex_glove = models.Glove.objects.get(name='Latex')
        self.assertIn(latex_glove, castor_oil.gloves.all())
        # Assigns an N/A for default NFPA rating
        self.assertEqual(
            castor_oil.health,
            models.Chemical.NFPA_NOT_AVAILABLE
        )
        # Test if formula numbers are subscripted
        magnesium_hydroxide = models.Chemical.objects.get(name='Magnesium Hydroxide')
        self.assertEqual(magnesium_hydroxide.formula, 'Mg(OH)_2')

    def test_convert_containers(self):
        # Delete current container list
        models.Container.objects.all().delete()
        self.convert_containers(self.containerfile)
        # Check first imported container
        container = models.Container.objects.first()
        self.assertEqual(container.chemical.name, 'Lithium')
        self.assertEqual(container.expiration_date, datetime.date(2015, 8, 7))
        self.assertEqual(container.chemical.cas_number, '7439-93-2')
        new_location = models.Location.objects.get(name='Glove Box @ 4163')
        self.assertEqual(container.location, new_location)
        self.assertEqual(container.batch, 'SZBE0200V')
        new_supplier = models.Supplier.objects.get(name='Sigma-Aldrich')
        self.assertEqual(container.supplier, new_supplier)
        self.assertEqual(container.state, 'Solid')
        self.assertEqual(container.container_type, 'Glass Bottle')
        self.assertEqual(container.owner.first_name, 'Mike')
        self.assertEqual(container.quantity, 25)
        self.assertEqual(container.unit_of_measure, 'g')
        # Check automatic comment
        today = datetime.date.today()
        expected_string = 'Imported from old inventory on {}'.format(
            today.strftime('%Y-%m-%d'))
        self.assertEqual(container.comment, expected_string)
