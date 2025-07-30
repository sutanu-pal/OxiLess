from django import forms

class CarbonForm(forms.Form):
    electricity_kwh = forms.FloatField(label="Monthly electricity usage (kWh)", min_value=0, required=True)
    region = forms.CharField(label="Region (e.g., Mumbai, India)", max_length=100, required=True)
    transport_km = forms.FloatField(label="Weekly travel distance (km)", min_value=0, required=True)
    vehicle_type = forms.ChoiceField(
        label="Primary transport mode",
        choices=[
            ('passenger_car_gasoline', 'Petrol Car'),
            ('passenger_car_diesel', 'Diesel Car'),
            ('passenger_car_electric', 'Electric Car'),
            ('bus', 'Bus'),
            ('train', 'Train'),
        ],
        required=True
    )
    flights_per_year = forms.IntegerField(label="Number of flights per year", min_value=0, required=True)
    flight_class = forms.ChoiceField(
        label="Flight class",
        choices=[
            ('economy', 'Economy'),
            ('business', 'Business'),
            ('first', 'First Class'),
        ],
        required=True
    )
    grocery_spend = forms.FloatField(label="Monthly grocery spend (USD)", min_value=0, required=True)
    diet_type = forms.ChoiceField(
        label="Diet type",
        choices=[
            ('meat_heavy', 'Meat-heavy'),
            ('mixed', 'Mixed'),
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
        ],
        required=True
    )
    purchase_spend = forms.FloatField(label="Monthly spend on goods (e.g., electronics, clothing, USD)", min_value=0, required=True)
    purchase_category = forms.CharField(label="Main purchase category (e.g., electronics, clothing)", max_length=100, required=True)
    home_type = forms.ChoiceField(
        label="Home type",
        choices=[
            ('apartment', 'Apartment'),
            ('house', 'House'),
            ('shared', 'Shared Living'),
        ],
        required=True
    )
    household_size = forms.IntegerField(label="Number of people in household", min_value=1, required=True)

class GroupForm(forms.Form):
    name = forms.CharField(label="Group Name", max_length=100, required=True)

class JoinGroupForm(forms.Form):
    code = forms.CharField(label="Group Code", max_length=10, required=True)