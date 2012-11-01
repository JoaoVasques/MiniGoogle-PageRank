'''
Created on Dec 3, 2011

@author: joaovasques
'''

from google.appengine.ext import db

class page(db.Model):
    '''
    classdocs
    '''
    name = db.StringProperty()
    page_rank = db.FloatProperty()

    def page_key(self,page_name=None):
        return db.Key.from_path('page',page_name)
#    def __init__(selfparams):
#        '''
#        Constructor
#        '''
#        