from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)
    alpha2Code = models.CharField(max_length=2)
    alpha3Code = models.CharField(max_length=3)
    population = models.IntegerField()
    capital = models.CharField(max_length=50, null=True, blank=True)
    topLevelDomain = models.ManyToManyField("TopLevelDomain", related_name="countries")

    region = models.ForeignKey(
        "Region",
        on_delete=models.CASCADE,
        related_name="countries",
    )

    def __str__(self):
        return self.name


class TopLevelDomain(models.Model):
    name = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
