from pandas import DataFrame

def parseYearFromDate(date: str) -> str:
    if '-' in date:
        split = date.split('-')
        if len(split) == 3:
            year, month, day = split
        elif len(split) == 2:
            year, month = split
        return year
            
    elif len(date) == 4:
        return date
    
    return ""

