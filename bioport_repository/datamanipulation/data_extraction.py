class BioDataExtractor:
    _guessable_values = [
        'geboortedatum',
        'sterfdatum',
        ] 
    def __init__(self, bio):
        """
        
        bio - a Biography instance
        """
        self.bio = bio
          
    def guess_value(self, k):
        assert k in self._guessable_values
        return None