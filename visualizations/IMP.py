import fastf1


# Getting Schedule Info

schedule = fastf1.get_event_schedule(2026)
print(schedule)
# print(schedule.columns) 

'''

[25 rows x 23 columns]
Index(['RoundNumber', 'Country', 'Location', 'OfficialEventName', 'EventDate',
       'EventName', 'EventFormat', 'Session1', 'Session1Date',
       'Session1DateUtc', 'Session2', 'Session2Date', 'Session2DateUtc',
       'Session3', 'Session3Date', 'Session3DateUtc', 'Session4',
       'Session4Date', 'Session4DateUtc', 'Session5', 'Session5Date',
       'Session5DateUtc', 'F1ApiSupport'],
      dtype='object')

'''

# Getting session info

# session = fastf1.get_session(2025,"Britain","R")
# session.load()
# print(session.session_info)

'''

{'Meeting': {'Key': 1277, 
'Name': 'British Grand Prix', 
'OfficialName': 'FORMULA 1 QATAR AIRWAYS BRITISH GRAND PRIX 2025', 
'Location': 'Silverstone', 
'Number': 12, 
'Country': {'Key': 2, 'Code': 'GBR', 'Name': 'United Kingdom'}, 
'Circuit': {'Key': 2, 'ShortName': 'Silverstone'}}, 
'SessionStatus': 'Inactive', 
'ArchiveStatus': {'Status': 'Generating'}, 
'Key': 9947, 
'Type': 'Race', 
'Name': 'Race', 
'StartDate': datetime.datetime(2025, 7, 6, 15, 0), 
'EndDate': datetime.datetime(2025, 7, 6, 17, 0), 
'GmtOffset': datetime.timedelta(seconds=3600), 
'Path': '2025/2025-07-06_British_Grand_Prix/2025-07-06_Race/'}

'''