import requests
from django.db import transaction
from django.core.management.base import BaseCommand

from countries.models import Country, Region, TopLevelDomain


class Command(BaseCommand):
    help = "Loads country data from a JSON file."

    ## Original Method
    # IMPORT_FILE = os.path.join(settings.BASE_DIR, "..", "data", "countries.json")
    # def get_data(self):
    #     with open(self.IMPORT_FILE) as f:
    #         data = json.load(f)
    #     return data

    ## New Method
    IMPORT_URL = "https://storage.googleapis.com/dcr-django-test/countries.json"

    def get_data(self):
        response = requests.get(self.IMPORT_URL)
        data = response.json()
        return data

    ## Original Method
    # def handle(self, *args, **options):
    #     data = self.get_data()
    #     for row in data:
    #         region, region_created = Region.objects.get_or_create(name=row["region"])
    #         if region_created:
    #             self.stdout.write(
    #                 self.style.SUCCESS("Region: {} - Created".format(region))
    #             )
    #         country, country_created = Country.objects.get_or_create(
    #             name=row["name"],
    #             defaults={
    #                 "alpha2Code": row["alpha2Code"],
    #                 "alpha3Code": row["alpha3Code"],
    #                 "population": row["population"],
    #                 "region": region,
    #             },
    #         )

    #         self.stdout.write(
    #             self.style.SUCCESS(
    #                 "{} - {}".format(
    #                     country, "Created" if country_created else "Updated"
    #                 )
    #             )
    #         )

    ## New Method
    def handle(self, *args, **options):
        data = self.get_data()

        with transaction.atomic():            
            # Regions
            region_names = set([row["region"] for row in data])
            existing_regions = {region.name: region for region in Region.objects.all()}
            new_regions = region_names - existing_regions.keys()
            deleted_regions = existing_regions.keys() - region_names
            
            # Create new Regions
            if new_regions:
                for name in new_regions:
                    if not name: # Skip empty values
                        raise ValueError("Empty region name")
                    region = Region(name=name)
                    region.save()
                    existing_regions[name] = region
                    self.stdout.write(
                        self.style.SUCCESS("Region: {} - Created".format(region))
                    )
            
            # Remove deleted Regions
            if deleted_regions:
                Region.objects.filter(name__in=deleted_regions).delete()
                for region_name in deleted_regions:
                    self.stdout.write(
                        self.style.SUCCESS("Region: {} - Deleted".format(region_name))
                    )

            # TopLevelDomains
            topLevelDomain_names = set([tld for row in data for tld in row["topLevelDomain"]])
            existing_topLevelDomains = {tld.name: tld for tld in TopLevelDomain.objects.all()}
            new_topLevelDomains = topLevelDomain_names - existing_topLevelDomains.keys()
            deleted_topLevelDomains = existing_topLevelDomains.keys() - topLevelDomain_names
            
            # Create new topLevelDomains
            if new_topLevelDomains:
                for name in new_topLevelDomains:
                    if not name: # Skip empty values such as in the case of Kosovo
                        continue
                    topLevelDomain = TopLevelDomain(name=name)
                    topLevelDomain.save() # Obtain id for new topLevelDomain
                    existing_topLevelDomains[name] = topLevelDomain
                    self.stdout.write(
                        self.style.SUCCESS("TopLevelDomain: {} - Created".format(topLevelDomain))
                    )

            # Remove deleted topLevelDomains
            if deleted_topLevelDomains:
                TopLevelDomain.objects.filter(name__in=deleted_topLevelDomains).delete()
                for topLevelDomain_name in deleted_topLevelDomains:
                    self.stdout.write(
                        self.style.SUCCESS("TopLevelDomain: {} - Deleted".format(topLevelDomain_name))
                    )
            
            # Countries
            country_names = set([row["name"] for row in data])
            existing_countries = {country.name: country for country in Country.objects.all()}
            deleted_countries = existing_countries.keys() - country_names
            
            # Create new or update countries
            for row in data:
                if row["name"] in existing_countries:
                    country, exists = existing_countries[row["name"]], True
                else:
                    if not row["name"]: # Skip empty values
                        continue
                    country, exists = Country(name=row["name"]), False
                country.alpha2Code = row["alpha2Code"]
                country.alpha3Code = row["alpha3Code"]
                country.population = row["population"]
                country.region = existing_regions[row["region"]]
                country.capital = row["capital"].strip() if row["capital"] else None # Add capital field if exists, otherwise set to None as in the case of Antarctica, the United States Minor Outlying Islands, and Macao.

                country.save()
                self.stdout.write(
                    self.style.SUCCESS("Country: {} - {}".format(country, "Created" if not exists else "Updated"))
                )

                # Handle updating the relationships with topLevelDomains
                country.topLevelDomain.clear() # Clear existing top level domains before re-adding them. This approach would be inefficient for densely interconnected objects but works ok for this case.
                for tld in row["topLevelDomain"]:
                    if tld:  # Skip empty values such as in the case of Kosovo
                        tld_obj = existing_topLevelDomains[tld]
                        country.topLevelDomain.add(tld_obj)
            
            # Remove deleted countries
            if deleted_countries:
                Country.objects.filter(name__in=deleted_countries).delete()
                for country_name in deleted_countries:
                    self.stdout.write(
                        self.style.SUCCESS("Country: {} - Deleted".format(country_name))
                    )
