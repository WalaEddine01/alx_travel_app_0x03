#!/usr/bin/python3
"""
"""
from django.core.management.base import BaseCommand
from ......models import Listing
import random

class Command(BaseCommand):
    help = 'Seed database with sample listings'

    def handle(self, *args, **kwargs):
        Listing.objects.all().delete()

        titles = ['Cozy Cabin', 'Beach House', 'Mountain Retreat', 'City Apartment', 'Country Villa']
        locations = ['Paris', 'New York', 'Tokyo', 'Cape Town', 'Sydney']

        for _ in range(10):
            listing = Listing.objects.create(
                title=random.choice(titles),
                description='This is a wonderful place to stay.',
                price_per_night=random.uniform(50, 300),
                location=random.choice(locations),
                available=random.choice([True, False])
            )
            self.stdout.write(self.style.SUCCESS(f'Created listing: {listing.title}'))

