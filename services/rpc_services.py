'''
Created on Dec 7, 2011

@author: joaovasques
'''

from protorpc import messages, message_types
from protorpc import remote
from google.appengine.ext import db
import logging

"""
Service nr 1: Get PageRank index
"""
class WebPage(messages.Message):
    name = messages.StringField(1)
    page_rank = messages.FloatField(2)
    

class PageRankIndex(messages.Message):
    index = messages.MessageField(WebPage,1,repeated=True)
    
class GetPageRankIndexService(remote.Service):
    
    @remote.method(message_types.VoidMessage,PageRankIndex)
    def get(self,request):
        
        query = db.GqlQuery("SELECT * "
                          "FROM pageInfo "
                          "ORDER BY page_rank DESC")
    
        pages = []
        existing_pages = {}        
    
        for page in query:
            p = page
            if existing_pages.has_key(p.page_name) == False:
                logging.debug("Name: %s Page Rank: %f" % (p.page_name,p.page_rank))            
                existing_pages[p.page_name]='exist'
                output_page = WebPage(name=p.page_name,page_rank = p.page_rank)
                pages.append(output_page)        
        
        
        return PageRankIndex(index=pages)

"""
Service nr 2: get Crawler output blobstore's key
"""
#class FileBlobstoreKey(messages.Message):
#    blobstore_key = messages.StringField(1)
#        
#class UploadCrawlerOutput(remote.Service):
#    
#    @remote.method(FileBlobstoreKey,message_types.VoidMessage)
#    def upload(self,request):
