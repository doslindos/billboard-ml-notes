from typing import Tuple
from pandas import concat, DataFrame

def sampleByYears(
    hits: DataFrame,
    nonHits: DataFrame,
    sampleSize: int,
    earliest: int,
    latest: int
    ) -> List[Optional[Any]]:

    hitSamples = None
    nonHitSamples = None
    count = 0
    # Loop all years that the dataset has
    for year in hits['year'].unique():
        
        # Check the processed year is outside the range of wanted years skip it
        if int(year) < earliest and int(year) > latest:
            continue
        
        # Take all songs by year
        allHitsInYear = hits[hits['year'] == year]
        allNotHitsInYear = nonHits[nonHits['year'] == year]
    
        # Take the samples
        hitSample = allHitsInYear.sample(sampleSize)
        notHitSample = allNotHitsInYear.sample(sampleSize)
    
        def addToDataset(samples: pandasSample, dataset: pandasSample) -> DataFrame:
            return concat([samples, dataset], ignore_index=True)
        
        hitSamples = hitSample if hitSamples is None else addToDataset(hitSamples, hitSample)
        notHitSamples = notHitSample if notHitSamples is None else addToDataset(notHitSamples, notHitSample)
    
    return [hitSamples, notHitSamples]
