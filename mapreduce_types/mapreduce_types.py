'''
Created on Nov 30, 2011

@author: joaovasques
'''

from google.appengine.ext import db

class WebPage(db.Model):
    '''
    classdocs
    '''
    name = "default_name"
    page_rank = 1
    outlinks = []
    
    #Surfer constant
    D_VALUE = 0.85
    NUMBER_OF_PAGES = 10

    def __init__(self,page_name, pr, outlinks):
        '''
        Constructor
        '''
        self.name = page_name
        self.outlinks = outlinks        
        self.page_rank = 1.0/self.NUMBER_OF_PAGES
        
        
    def toString(self):
        return "Name: %s PageRank: %f Outlinks: %s" % (self.name,self.page_rank,str(self.outlinks))
    
    """
    inlinks format - list of WebPages
    """
    
    def updatePageRank(self,inlinks):
        new_page_rank = 0.0
        
        for inlink in inlinks:
            i = WebPage("",0,[])
            i = inlink
            new_page_rank = new_page_rank + (i.page_rank/len(i.outlinks))
        
        new_page_rank = new_page_rank * self.D_VALUE
        new_page_rank = new_page_rank + (1-self.D_VALUE)/self.NUMBER_OF_PAGES
        
        self.page_rank = new_page_rank