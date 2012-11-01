#!/usr/bin/env python

from __future__ import with_statement
from mapreduce_types.mapreduce_types import WebPage
from persistence import page
from protorpc.webapp import service_handlers
from services.rpc_services import GetPageRankIndexService


__author__ = """joao.vasques@ist.utl.pt (Joao Vasques) - special thanks to Mike Aizatsky"""

import logging
import re
import urllib2

from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import webapp

from google.appengine.ext.webapp import util

from mapreduce.lib import files

from mapreduce import base_handler
from mapreduce import mapreduce_pipeline

#Persistence
class pageInfo(db.Model):
    '''
    classdocs
    '''
    page_name = db.StringProperty()
    page_rank = db.FloatProperty()


def page_key(page_name=None):
    return db.Key.from_path('page',page_name)


class WebSiteInfo(db.Model):
   url = db.StringProperty()
   pageRank = db.FloatProperty()
   title = db.StringProperty()
   description = db.StringProperty(multiline=True)
   htmlBlobStorePath = db.StringProperty()
   textBlobStorePath  = db.StringProperty()  
   keyWords = db.ListProperty
   siteLinks = db.StringProperty()
   mediaLinks = db.ListProperty

class IndexHandler(webapp.RequestHandler):
  """The main page that users will interact with, which presents users with
  the ability to upload new data or run MapReduce jobs on their existing data.
  """

  webpages = {}
  webpages['Cooking'] = "http://en.wikipedia.org/wiki/Cooking"
  webpages['Elliptical'] = "http://en.wikipedia.org/wiki/Elliptical_galaxies" 
  webpages['Food'] = "http://en.wikipedia.org/wiki/Food"
  webpages['Humus'] = "http://en.wikipedia.org/wiki/Humus" 
  webpages['Iron'] ="http://en.wikipedia.org/wiki/Iron"
  webpages['Nutrient'] = "http://en.wikipedia.org/wiki/Nutrients" 
  webpages['Plant'] = "http://en.wikipedia.org/wiki/Plant_nutrition"
  webpages['Protein'] = "http://en.wikipedia.org/wiki/Proteins"
  webpages['supernova'] ="http://en.wikipedia.org/wiki/Type_II_supernova" 
  webpages['Vitamin'] = "http://en.wikipedia.org/wiki/Vitamins"
  webpages['Google'] = "http://www.google.pt/"
  
  def get(self):

    filekey = self.request.get("filekey")
    
    #key = ManageCrawlerOutput.requestCrawlerOutput(self)
#    str_key = str(key)

    self.response.headers['Content-Type'] = 'text/plain'
    
    query = db.GqlQuery("SELECT * FROM WebSiteInfo")
    
    file_name = files.blobstore.create(mime_type='application/octet-stream')

    with files.open(file_name, 'a') as f:              
        for q in query:
            w = WebSiteInfo()
            w=q
            title = str(w.title)
            title = re.sub(r" ", "", title)
            #title.replace(" ","-")
            self.response.out.write("parsed title %s\n" % title)
            f.write("%s %s\n" % (title,w.siteLinks))

    files.finalize(file_name)
    logging.debug("File saved successfully")
    
    key = files.blobstore.get_blob_key(file_name)

#    info = blobstore.get(key)
#    reader = info.open()
#    file_content = reader.read(501900)
#    self.response.out.write("\n\n")
#    self.response.out.write("%s" % file_content)


    pipeline = PageRankPipeline(filekey, str(key))      
    pipeline.start()
    
    self.redirect(pipeline.base_path + "/status?root=" + pipeline.pipeline_id)


  def post(self):
    filekey = self.request.get("filekey")
    
    key = ManageCrawlerOutput.requestCrawlerOutput(self)
    
    str_key = str(key)

    pipeline = PageRankPipeline(filekey, str_key)#key)#blob_key)      
    pipeline.start()
    
    self.redirect(pipeline.base_path + "/status?root=" + pipeline.pipeline_id)


def split_into_sentences(s):
  """Split text into list of sentences."""
  s = re.sub(r"\s+", " ", s)
  s = re.sub(r"[\\.\\?\\!]", "\n", s)
  return s.split("\n")


def split_into_words(s):
  """Split a sentence into list of words."""
  s = re.sub(r"\W+", " ", s)
  s = re.sub(r"[_0-9]+", " ", s)
  return s.split()

"""Returns a list of dictionaries. Each dictionary represents the content of the line"""
def parse_crawler_output(output):
    """Dictionary structure
        dic['NAME'] = page name
        dic['PAGE_RANK'] = page's page rank value
        dic['OUTLINKS'] = list(outlinks)
    """
    
    #gets a list with all the lines
    contents = output.split(" ")
    
    line_content = []
    
    page_name = contents[0]
    outlinks = []
    i=1
    #fills line_content with webpage that represent the line content
    for line in contents:
        
        if i <= 2:
            i=i+1
            continue
        #ignore blank lines
        if len(line) == 0:
            continue

        outlinks.append(line)

        
    webpage_info = WebPage(page_name,1,outlinks)
    line_content.append(webpage_info) 
    return line_content    

#Page Rank Mapper
def pagerank_map(data):
  """Page Rank map function."""
  text = data[1]#text_fn()
  
#  if int(data[0]) == 0:
#      WebPage.NUMBER_OF_PAGES = int(data[1])
#      return
#  
  line_content = parse_crawler_output(text)


  for l in line_content:
      p = WebPage("",0,[])
      p = l
      
      for outlink in p.outlinks:
          mapper_value = {}
          mapper_value['PAGE_NAME'] = p.name
          mapper_value['PAGE_RANK'] = p.page_rank
          mapper_value['OUTLINKS'] = p.outlinks
                    
          yield(outlink,mapper_value)
          

#Page Rank Reducer
def pagerank_reduce(key, values):
  """Page Rank reduce function.
     key - page name
     values = list of dictionaries(web page info)
  """
  
  inlinks = []
  
  for value in values:
      dic = {}
      dic = eval('dict(%s)'% value)
      inlink = WebPage("",0,[])      
      for (k,v) in dic.items():
          if k == 'PAGE_NAME':
              inlink.name = v
          elif k == 'PAGE_RANK':
              inlink.page_rank = v
          else :
              inlink.outlinks = v
    
      inlinks.append(inlink)
  
  webpage = WebPage(key,0,[])
  webpage.updatePageRank(inlinks)
  
  #store web page info on the database
  p = pageInfo(page_key(webpage.name))
  p.page_name = webpage.name
  p.page_rank = webpage.page_rank
  yield db.put(p)


#Page Rank Pipeline
class PageRankPipeline(base_handler.PipelineBase):
  """A pipeline to run Page Rank.

  Args:
    To be defined 
  """

  def run(self, filekey, blobkey):  
    output = yield mapreduce_pipeline.MapreducePipeline(
        "pagerank",
        "main.pagerank_map",
        "main.pagerank_reduce",
        "mapreduce.input_readers.BlobstoreLineInputReader",
        "mapreduce.output_writers.BlobstoreOutputWriter",
        mapper_params={
            "blob_keys": blobkey,
        },
        reducer_params={
            "mime_type": "text/plain",
        },
        shards=10)
    

class ManageCrawlerOutput(object):
    
    crawler_file_name = "default"
    
    @staticmethod    
    def requestCrawlerOutput(self):
        
        
        logging.debug("Request Crawler Output")
        
        file_content = 'DEFAULT_CONTENT'
        
        url = "http://web.ist.utl.pt/ist163512/crawler.txt"
        result = urllib2.urlopen(url)
        file_content = result.read()
        
        file_name = files.blobstore.create(mime_type='application/octet-stream')
        self.crawler_file_name = file_name
        
        with files.open(file_name, 'a') as f:
            f.write("%s" % file_content)
            
        files.finalize(file_name)
        logging.debug("File saved successfully")
        key = files.blobstore.get_blob_key(file_name)
        return key
    
    @staticmethod
    def getCrawlerFile(self):
        
        logging.debug("Get Crawler file from blobstore")
            
        key = files.blobstore.get_blob_key(self.crawler_file_name)
        info = blobstore.get(key)
        reader = info.open()
        file_content = reader.read(1024)
        logging.debug("Returning file")
        return file_content

class GetPageRankIndex(webapp.RequestHandler):
    
    def get(self):
        
        logging.debug("Get PageRank index")
        logging.debug("Querying the database...")
        
        query = db.GqlQuery("SELECT * "
                          "FROM pageInfo "
                          "ORDER BY page_rank DESC")
    
        pages = []
        existing_pages = {}    
        self.response.headers['Content-Type'] = '/text/plain'
        self.response.headers['Content-Disposition'] = 'attachment; filename=index.txt'
    
        logging.debug("Success")
        total=0.0
        for page in query:
            p = pageInfo()
            p = page
            
            if existing_pages.has_key(p.page_name) == False:
                existing_pages[p.page_name]='exist'
                pages.append(p)
                total = total + p.page_rank
                                                         
        for p in pages:
            self.response.out.write("%s %f\n" % (p.page_name,p.page_rank))
        self.response.out.write("Total %f" % total)    

service_mapping = service_handlers.service_mapping([('/getindex',GetPageRankIndexService),])

APP = webapp.WSGIApplication(
    [
        ('/', IndexHandler),
        ('/page-rank-index',GetPageRankIndex),
    ]+service_mapping,
    debug=True)

def main():
    
  logging.getLogger().setLevel(logging.DEBUG) 
  util.run_wsgi_app(APP)

if __name__ == '__main__':
  main()
