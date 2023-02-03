import requests
import pandas
import json
import us
import ipywidgets
import matplotlib

#Dictionary of Census columns
censusDict = {
'B01003_001E': 'Total Population',
'B01001_002E': 'Male',
'B01001_026E': 'Female',
'B02008_001E': 'White',
'B02009_001E': 'Black',
'B02010_001E': 'AIAN',
'B02011_001E': 'Asian',
'B02012_001E': 'NHPI',
'B02013_001E': 'Some Other Race',
'B03001_002E': 'Nonhispanic',
'B03001_003E': 'Hispanic',
'B06011_001E': 'Median Income',
'B06012_002E': 'Below poverty level',
'B06012_003E': 'Below 1.5 poverty level',
'B23025_003E': 'Labor force',
'B23025_004E': 'Employed',
'B23025_005E': 'Unemployed',
'B01001_003E': 'Male 0-4',
'B01001_004E': 'Male 5-9',
'B01001_005E': 'Male 10-14',
'B01001_006E': 'Male 15-17',
'B01001_007E': 'Male 18-19',
'B01001_008E': 'Male 20',
'B01001_009E': 'Male 21',
'B01001_010E': 'Male 22-24',
'B01001_011E': 'Male 25-29',
'B01001_012E': 'Male 30-34',
'B01001_013E': 'Male 35-39',
'B01001_014E': 'Male 40-44',
'B01001_015E': 'Male 45-49',
'B01001_016E': 'Male 50-54',
'B01001_017E': 'Male 55-59'
}

#Returns a data frame of census Data
def fetchCensusData(api_key):
    year='2020'
    dsource='acs' # the survey i.e. decennial census, acs, etc
    dseries='acs5' # a dataset within the survey
    cols="NAME,"+','.join(censusDict.keys())
    state='*' # ansi fips codes for states; use asterisk * for all states
    place='*' # ansi fips codes cities / towns; use asterisk * for all places
    base_url = f'https://api.census.gov/data/{year}/{dsource}/{dseries}'
    data_url = f'{base_url}?get={cols}&for=place:{place}&in=state:{state}&key={api_key}'

    raw = requests.get(data_url).text
    #Make sure the request went through
    if raw.find('Invalid Key',0,100) != -1:
        return pandas.DataFrame()

    #else unpack the json
    data = json.loads(raw)

    #The first entry has the column headers
    columns = data.pop(0)
    #Load into a dataframe
    df=pandas.DataFrame(data, columns=columns)
    #Rename using our dictionary
    df.rename(columns=censusDict, inplace=True)
    #Look up the postal code abbreviations for the states
    df['State Code']= df.apply(lambda row: us.states.lookup(str(row['state'])).abbr, axis=1)
    df=df.set_index('NAME')
    return df

class censusDataFetcher:
    townRace = pandas.DataFrame()
    censusData = pandas.DataFrame()
    def __init__(self, outputWidget0, outputWidget1):
        outputWidget0.clear_output()
        outputWidget1.clear_output()

        apiText = ipywidgets.Text()
        stateDropDown = ipywidgets.Dropdown()
        placeDropDown = ipywidgets.Dropdown()
        statusBox = ipywidgets.VBox()
        fetchButton = ipywidgets.Button(description="Fetch Census Data")

        self.townRace['Race']=["White","Black or African American", "American Indian or Alaskan Native", "Asian", "Native Hawaiian or Other Pacific Islander", "Some Other Race"]

        with outputWidget0:
            display(ipywidgets.HBox([ipywidgets.Label("Enter your census API Key:"), apiText]))
            display(fetchButton)
            display(statusBox)
            display(ipywidgets.HBox([ipywidgets.Label("Select the state your town is in:"),stateDropDown]))
            display(ipywidgets.HBox([ipywidgets.Label("Select your town: "),placeDropDown]))

        fetchButton.on_click(lambda b: fetchClick(apiText.value))
        def fetchClick(api_key):
            statusBox.children += (ipywidgets.Label("Fetching with census key " + api_key + " ... (this may take a moment)"),)
            self.censusData = fetchCensusData(api_key)
            statusBox.children+= (ipywidgets.Label("Complete!"),)
            if not self.censusData.empty:
                stateDropDown.options = self.censusData.groupby('State Code').groups.keys()
    
        stateDropDown.observe(lambda b: stateSelected(), names='value')
        def stateSelected():
            placeDropDown.options = sorted(self.censusData[self.censusData['State Code']==stateDropDown.value].index.values.tolist())
    
        placeDropDown.observe(lambda b: placeSelected(), names='value')
        def placeSelected():
            self.townRace['Population'] = [self.censusData.loc[placeDropDown.value]['White'],
                                            self.censusData.loc[placeDropDown.value]['Black'],
                                            self.censusData.loc[placeDropDown.value]['AIAN'],
                                            self.censusData.loc[placeDropDown.value]['Asian'],
                                            self.censusData.loc[placeDropDown.value]['NHPI'],
                                            self.censusData.loc[placeDropDown.value]['Some Other Race'] ]
            self.townRace['Population']=self.townRace['Population'].astype('int')
            self.townRace['Percentage']=self.townRace['Population']/int(self.censusData.loc[placeDropDown.value]['Total Population'])
    
            #Show a plot
            outputWidget1.clear_output()
            with outputWidget1:
                display("The total population of " + placeDropDown.value + " is " + self.censusData.loc[placeDropDown.value]['Total Population'])
                self.townRace.plot.bar(x='Race',y='Percentage')
                matplotlib.pyplot.show()



