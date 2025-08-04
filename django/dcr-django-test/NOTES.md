# Digital Control Room - Django Test

## Setup

The instructions below are for use with venv, but of course you can setup the project however is most comfortable for you (virtualenv, pipenv, etc.). You will need python3.5+ to run this code.

```bash
python3 -m venv dcr-django-test-env
source dcr-django-test-env/bin/activate

cd dcr-django-test
pip install -r requirements.txt

cd testsite
python manage.py runserver
python manage.py update_country_listing
python manage.py test
```

## Exercises

### Exercise 1 - Complete Stats View

http://localhost:8000/countries/stats/ currently returns an empty JSON response, this should be updated to provide a list of regions. 

Each region object should contain:
 * The region's name
 * The number of countries in that region (a simple count)
 * The total population of the region (the sum of the population of each country)

The output format should be:
```json
{
    "regions": [
        {
        "name": "Africa",
        "number_countries": xxx,
        "total_population": xxx
        },
        {
        "name": "Americas",
        "number_countries": xxx,
        "total_population": xxx
        },
        ...
    ]
}
```
#### Notes:

It is super important to use the annotate() method here. It allows us to frontload the calculations for the aggregated properties for each region as part of the database query, meaning that the query will only be executed once. Not using this method would result in a N+1 query problem, where the aggregation query is executed for each region as well as the regions themselves. Additional efficiency is gained by constructing the precise representation that is required for the response in the query, taking the values 'name', 'number_countries' and 'total_population' from the queryset, which results in less data transfer from the database. Finally, ordering by name ensures consistent results.

### Exercise 2 - Integrate with API

The management command:
```bash
python manage.py update_country_listing
```
currently updates the models from a local JSON file. Please update this management command to obtain the JSON input data from this url:  
https://storage.googleapis.com/dcr-django-test/countries.json

#### Notes: 
We may simply overwrite the get_data() method with one that requests the data from the url.
Url is requested using the requests library, the response.json() is then parsed and the data is returned to the management command.

### Exercise 3 - Store additional Data

The management command:
```bash
python manage.py update_country_listing
```
currently extracts and stores the data:
 * name
 * alpha2Code
 * alpha3Code
 * population
 * region

Please update the models and management command to also import:
 * topLevelDomain
 * capital

#### Notes:
- Examining the data returned from the url request, we can see that both 'topLevelDomain' and 'capital' are unnested fields that are always present in the schema.

- 'topLevelDomain' is presented as a list.
    - Only one country does not have a topLevelDomain, which is Kosovo. The value for their topLevelDomain is an empty string.
    - In the case of only three countries ('Bonaire, Sint Eustatius and Saba', 'Kazakhstan', and 'Saint Martin (French part)') does the country's topLevelDomain have more than one element.
        - In the case of Saint Martin (French part), they have an exclusive topLevelDomain as ".mf" while the other two are ".fr" (shared with France) and ".gp" (shared with Guadeloupe).
        - Similarly, the country 'Bonaire, Sint Eustatius and Saba' has an exclusive topLevelDomain as ".an" while the other is ".nl" (shared with Netherlands).
        - Kazakhstan's topLevelDomains (".kz", ".қаз") are both exclusive.
    - With the exceptions of the one topLevelDomain for Kazakhstan, ".қаз", and Kosovo, which is an empty string, the length of any topLevelDomain is 3, matching the regex pattern "\.\w{2}"
    - We could ignore these discrepancies and take the first value of each topLevelDomain list, and define our field as a CharField with a max_length of 3 and also has null and blank set to True, to accommodate for Kosovo.
    - We could also define our field as a JSONField and store the topLevelDomain list as is. This would allow us to maintain the integrity of the data, but would require us to define a custom serializer and deserializer for the field.
    - We could also externalise the values in each topLevelDomain list to a separate table and define a ManyToMany relationship between the Country and TopLevelDomain models. We will take this approach.

- 'capital' is presented as a string.
    - Several "countries" do not have a capital - Antarctica, the United States Minor Outlying Islands, and Macao. In these cases, the values are empty strings.
    - The largest length of the capital string is 19, "Brunei Darussalam."
    - Interestingly, despite many countries having more than one capital (e.g. South Africa), the data shows only one of these in each capital field.
    - We can accommodate these values by defining our field as a CharField with a max_length of 50 and also has null and blank set to True.

The current implementation iterates over the data and uses the get_or_create() method to create new objects. Firstly, this does not update the objects, which is what we need to do for the new capital field. Secondly, it makes a get_or_create() request for each iteration for the region as well as the country, which is not efficient and introduces scaling problems. Finally, if we assume that the data being retrieved represents a complete updated dataset, while new objects are added, deleted objects are not removed.  
A better solution would use transaction.atomic() and the bulk_create()/bulk_update() methods where possible, and to treat the Region, Country and the new topLevelDomain models distinctly.

Region model:
- Being that the Region model has only the name field, we can simply create new regions from the data where the region name is not already present in the database; updating these objects is otherwise redundant.
- One limitation of this approach is that the values within the data are not validated, and so it is possible that regions will be created in error such as in the case of misspellings. We cannot ensure correct data within the scope of this project, it is the responsibility of the data provider.
- After the new regions have been created we construct a dictionary of region name to region object, which is necessary for updating the region field on the Country model.

TopLevelDomain model:
- We can also create new topLevelDomains in this way, but must assign the many-to-many relationships between the Country and TopLevelDomain models after these Country objects have been also created/updated.
- We should also delete topLevelDomains that no longer appear in the data.

Country model:
- We can take a similar approach to creating the missing Country data as we did with the Region model, predicated on the name field, but this must be extended with updating of the other values, which will require iteration. This does allow us to create or update these objects accordingly, familiar to the previous implementation, but altered so that the number of queries is reduced.
- We should also delete countries that no longer appear in the data. While it is unlikely for a country to be deleted, countries do change their names (e.g. Czechia, Türkiye) and as country names are the primary way of recognising Country objects (while not being the primary key), in the cases of name changes it is easiest to create a new country object and delete the old one.
- Acknowledging the possibility of name changes also exposes the same issue as with regions in which country names are not validated, and so misspelled country names will result in faulty country objects being created.