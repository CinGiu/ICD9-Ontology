from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
import tornado.ioloop
import tornado.web
import json
from urllib import urlopen
from lxml import etree
import os

ontology = etree.parse("ontology.owl") 

class Disease:
	def __init__(self,icdcm,label,score,parent_class,parent_label, parent_path):
		self.icdcm = icdcm
		self.label = label
		self.score = score
		self.parent_class = parent_class
		self.parent_label = parent_label
		self.parent_path  =  parent_path
		self.sibiling = [] 

#~ INIZIO gestione Server 
class HelloHandler(RequestHandler):
    def get(self):
		 self.render("index.html")

class SearchHandler(RequestHandler):
	def post(self):
		q = self.get_argument("q",None)
		num_result = self.get_argument("num_result",None)
		list_disease = get_disease(q, ontology)
		self.render("search.html",q=q.upper(),list_disease=list_disease, num_result = int(num_result))
		
def make_app():
	settings = {
		"static_path": os.path.join(os.path.dirname(__file__), "static"),
	}
	return Application([
        url(r"/", HelloHandler),
        url(r"/search", SearchHandler),
        ], **settings)

def main():
	app = make_app()
	app.listen(8888)
	print "started"
	IOLoop.current().start()


#~ FINE gestione Server


def get_disease(q, ontology):
	resp = urlopen("http://130.136.143.12:8890/codes?q="+q).read()
	dec = json.loads(resp)

	root = ontology.getroot()

	#~ Definizione namespace per ontologia
	owl = root.nsmap.get('owl')
	rdf = root.nsmap.get('rdf')
	rdfs = root.nsmap.get('rdfs')
	none = root.nsmap.get(None)
	
	#~ Array di supporto 
	parent_vector = []
	#~ 
	list_disease = []

	for item in dec:
		
		icdcm = item["id"]
		score = item["score"]
		label = item["titolo"]
		parent_class = ""
		parent_label = ""
		
		if (len(icdcm) > 3):
			icdcm = icdcm[:3]+"."+icdcm[3:]
			
		for node in root.xpath('a:Class/b:C_BASECODE/text()[. = "ICD9CM:'+icdcm+'"]', namespaces={'a': owl, 'b' : none}):
			parent_class = node.getparent().getparent().iterfind('a:subClassOf', namespaces={'a': rdfs}).next().items()
			if not parent_class:
				parent_class = node.getparent().getparent().iterfind('a:subClassOf/b:Class', namespaces={'a': rdfs, 'b':owl}).next().items()
			parent_class = parent_class[0][1]
		
		parent_label = root.iterfind('a:Class[@b:about="'+parent_class+'"]/c:label',namespaces={'a': owl, 'b':rdf,'c':rdfs}).next().text
		#~ parent_label = parent_label.lower()		
		parent_label = parent_label.title()	
		
		
			
		if parent_class not in parent_vector:
			parent_vector.append(parent_class)
			parent_path = root.iterfind('a:Class[@b:about="'+parent_class+'"]/c:C_FULLNAME',namespaces={'a': owl, 'b':rdf, 'c' : none}).next().text
			parent_path = parent_path.replace("\i2b2\Diagnoses\ICD9CM\\","Diagnoses / ")
			parent_path = parent_path.replace("\\"," / ")
			parent_path = parent_path.title()
			list_disease.append(Disease(icdcm,label,score,parent_class,parent_label,parent_path))
		else:
			for exitent in list_disease:
				if exitent.parent_class == parent_class:
					exitent.sibiling.append(Disease(icdcm,label,score,parent_class,parent_label,""))
	
	return list_disease
		
			
def print_result(q, ontology):
	list_disease = get_disease(q)
	for result in list_disease:
		print result.parent_label+" ---- icdn9 "+result.label+" score %.6f" % result.score	

main()
