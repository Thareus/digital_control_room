from io import StringIO
import json
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from countries.models import Country, Region, TopLevelDomain


class UpdateCountryListingTest(TestCase):
    """Tests for the update_country_listing management command."""

    def setUp(self):
        # Setup test data
        self.region1 = Region.objects.create(name='Europe')
        self.region2 = Region.objects.create(name='Americas')
        
        self.tld1 = TopLevelDomain.objects.create(name='.uk')
        self.tld2 = TopLevelDomain.objects.create(name='.us')
        
        # Create a country with related objects
        self.country1 = Country.objects.create(
            name='United Kingdom',
            alpha2Code='GB',
            alpha3Code='GBR',
            population=67886011,
            region=self.region1,
            capital='London'
        )
        self.country1.topLevelDomain.add(self.tld1)
        
        # Sample JSON data that would be returned by the API
        self.test_data = [
            {
                'name': 'United Kingdom',
                'alpha2Code': 'GB',
                'alpha3Code': 'GBR',
                'population': 67886012,  # Updated population
                'region': 'Europe',
                'topLevelDomain': ['.uk', '.gb'],  # Added .gb
                'capital': 'London'
            },
            {
                'name': 'United States',
                'alpha2Code': 'US',
                'alpha3Code': 'USA',
                'population': 331002651,
                'region': 'Americas',
                'topLevelDomain': ['.com'],
                'capital': 'Washington, D.C.'
            },
            {
                'name': 'Germany',
                'alpha2Code': 'DE',
                'alpha3Code': 'DEU',
                'population': 83240525,
                'region': 'Europe',
                'topLevelDomain': ['.de'],
                'capital': 'Berlin'
            }
        ]

    def test_handle_creates_new_country(self):
        """Test that new countries are created correctly."""
        # Germany doesn't exist in the initial setup
        self.assertFalse(Country.objects.filter(name='Germany').exists())
        
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=self.test_data):
            out = StringIO()
            call_command('update_country_listing', stdout=out)
            
        # Verify Germany was created
        germany = Country.objects.get(name='Germany')
        self.assertEqual(germany.alpha2Code, 'DE')
        self.assertEqual(germany.population, 83240525)
        self.assertEqual(germany.region.name, 'Europe')
        self.assertEqual(set(germany.topLevelDomain.values_list('name', flat=True)), {'.de'})
        
        # Verify output contains success message
        self.assertIn('Germany - Created', out.getvalue())

    def test_handle_updates_existing_country(self):
        """Test that existing countries are updated correctly."""
        uk = Country.objects.get(name='United Kingdom')
        self.assertEqual(uk.population, 67886011) # Population was 67886011 in setup, 67886012 in test data
        
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=self.test_data):
            out = StringIO()
            call_command('update_country_listing', stdout=out)
            
        # Verify UK was updated
        uk.refresh_from_db()
        self.assertEqual(uk.population, 67886012)
        self.assertEqual(uk.capital, 'London')
        self.assertEqual(set(uk.topLevelDomain.values_list('name', flat=True)), {'.uk', '.gb'})
        
        # Verify output contains update message
        self.assertIn('United Kingdom - Updated', out.getvalue())

    def test_handle_creates_new_region(self):
        """Test that new regions are created when needed."""
        # Asia doesn't exist in the initial setup
        self.assertFalse(Region.objects.filter(name='Asia').exists())
        
        # Add a country with a new region
        test_data = self.test_data + [{
            'name': 'Japan',
            'alpha2Code': 'JP',
            'alpha3Code': 'JPN',
            'population': 126476461,
            'region': 'Asia',
            'topLevelDomain': ['.jp'],
            'capital': 'Tokyo'
        }]
        
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=test_data):
            out = StringIO()
            call_command('update_country_listing', stdout=out)
            
        # Verify Asia was created
        self.assertTrue(Region.objects.filter(name='Asia').exists())
        self.assertIn('Region: Asia - Created', out.getvalue())

    def test_handle_manages_top_level_domains(self):
        """Test that TLDs are added and removed correctly."""
        # .gb is new, .us should be removed as it's not in test data
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=self.test_data):
            out = StringIO()
            call_command('update_country_listing', stdout=out)

        # Verify .gb was added
        self.assertTrue(TopLevelDomain.objects.filter(name='.gb').exists())
        self.assertIn('TopLevelDomain: .gb - Created', out.getvalue())
        
        # Verify .us was removed (it was in setup but not in test data)
        self.assertFalse(TopLevelDomain.objects.filter(name='.us').exists())
        self.assertIn('TopLevelDomain: .us - Deleted', out.getvalue())

    def test_handle_transaction_rollback(self):
        """Test that the transaction is rolled back on error."""
        # Create test data that will cause an error
        test_data = self.test_data + [{
            'name': 'Gibraltar',
            'alpha2Code': 'GB',
            'alpha3Code': 'GIB',
            'population': None, # Missing population 
            'region': 'Europe',
            'topLevelDomain': ['.gi'],
            'capital': 'Gibraltar'
        }]
        
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=test_data):
            with self.assertRaises(Exception):
                call_command('update_country_listing')
        
        # Verify that no new countries were created (transaction rolled back)
        self.assertEqual(Country.objects.count(), 1)  # Only the one from setUp
        self.assertFalse(Country.objects.filter(name='Germany').exists())

class OutliersTest(TestCase):
    """Tests for edge cases and special conditions in the country data.
    
    Uses TestCase with transaction handling to ensure proper test isolation.
    """
    @classmethod
    def setUpTestData(cls):
        """Load test data once for all test methods."""
        super().setUpTestData()
        test_data = json.load(open('countries/tests/test_data.json'))
        with patch('countries.management.commands.update_country_listing.Command.get_data', 
                  return_value=test_data):
            call_command('update_country_listing')
        
    def setUp(self):
        """Refresh objects from database to ensure we have the latest state."""
        super().setUp()
    
    def test_capitals(self):
        antarctica = Country.objects.get(name="Antarctica")
        assert antarctica.capital is None

        us_minor_islands = Country.objects.get(name="United States Minor Outlying Islands")
        assert us_minor_islands.capital is None

        macao = Country.objects.get(name="Macao")
        assert macao.capital is None

    def test_topLevelDomains(self):
        # Multiple TLDs for Kazakhstan, Saint Martin (French part), Bonaire, Sint Eustatius and Saba
        kazakhstan = Country.objects.get(name="Kazakhstan")
        assert kazakhstan.topLevelDomain.count() == 2
        expected_output = {".kz", ".қаз"}
        actual_output = set(kazakhstan.topLevelDomain.all().values_list('name', flat=True))
        assert expected_output == actual_output
        
        saint_martin = Country.objects.get(name="Saint Martin (French part)")
        assert saint_martin.topLevelDomain.count() == 3
        expected_output = {".mf", ".fr", ".gp"}
        actual_output = set(saint_martin.topLevelDomain.all().values_list('name', flat=True))
        assert expected_output == actual_output

        bonaire = Country.objects.get(name="Bonaire, Sint Eustatius and Saba")
        assert bonaire.topLevelDomain.count() == 2
        expected_output = {".an", ".nl"}
        actual_output = set(bonaire.topLevelDomain.all().values_list('name', flat=True))
        assert expected_output == actual_output

        # No TLDs for Kosovo
        kosovo = Country.objects.get(name="Republic of Kosovo")
        assert kosovo.topLevelDomain.count() == 0

        # TLD for Saint Martin (French part) and France is shared
        tld_fr = TopLevelDomain.objects.get(name=".fr")
        assert tld_fr.countries.count() == 2
        expected_output = {"France", "Saint Martin (French part)"}
        actual_output = set(tld_fr.countries.all().values_list('name', flat=True))
        assert expected_output == actual_output

        # TLD for Saint Martin (French part) and Guadeloupe is shared
        tld_gp = TopLevelDomain.objects.get(name=".gp")
        assert tld_gp.countries.count() == 2
        expected_output = {"Saint Martin (French part)", "Guadeloupe"}
        actual_output = set(tld_gp.countries.all().values_list('name', flat=True))
        assert expected_output == actual_output

        # TLD for Bonaire, Sint Eustatius and Saba and Netherlands is shared
        tld_nl = TopLevelDomain.objects.get(name=".nl")
        assert tld_nl.countries.count() == 2
        expected_output = {"Netherlands", "Bonaire, Sint Eustatius and Saba"}
        actual_output = set(tld_nl.countries.all().values_list('name', flat=True))
        assert expected_output == actual_output