# Google Maps Key

This project uses Google Maps. Each instance of Google Maps requires an API key to make it functional. This is quick guide to setting up your own key.

## Getting the API Key

1. Go to [Google API Console](https://console.developers.google.com/)

2. If it's the first time, click 'Next' on a bunch of pop-ups or just click somewhere where the pop-ups aren't

3. Create Credentials

   ![Credentials](../_static/img/rTzIfVp.png)
   - Select a project: Create a project
   - Project name: Anything you want
   - Yes/No for email
   - Yes to agree to ToS
   - Click create.

4. Get your API Key
   - Click on Credentials again
   - Click Create -> API
   - Choose 'Browser Key'
   - Click 'Create' and then copy the API Key somewhere
   ![API Browser Key](../_static/img/csEFWKd.png)
   ![API Browser Key](../_static/img/6upJVIr.png)

5. Enable five Google Maps APIs
   - Google Maps Javascript API - Enables Displaying of Map
     - Click on 'Library'
     - Type 'JavaScript' in the search box
     - Choose 'Google Maps Javascript API'
     - Click 'ENABLE'
   - Google Places API Web Service - Enables Location Searching
     - Click on 'Library'
     - Type 'Places' in the search box
     - Choose 'Google Places API Web Service'
     - Click 'ENABLE'
   - Google Maps Elevation API - Enables fetching of altitude
     - Click on 'Library'
     - Type 'Elevation' in the search box
     - Choose 'Google Maps Elevation API'
     - Click 'ENABLE'
   - Google Maps Geocoding API - Enables geocoding and reverse geocoding
     - Click on 'Library'
     - Type 'Geocoding' in the search box
     - Choose 'Google Maps Geocoding API'
     - Click 'ENABLE'
   - Google Maps Time Zone API - Enables time zone for a location
     - Click on 'Library'
     - Type 'Time Zone' in the search box
     - Choose 'Google Maps Time Zone API'
     - Click 'ENABLE'

## Using the API Key

The google maps api key may either be installed in `config/config.ini` file, or you can provide it as a command line parameter like `-k 'your key here'`
