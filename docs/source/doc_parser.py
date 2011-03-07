import os
import sys
import inspect

API_DOC_HEADER = """
.. Doc page generated by doc_parser.py

Auto-Generated API Docs
=======================

.. toctree::
	:maxdepth: 2

"""

AUTODOC_STRING = """
.. automodule:: %s
	:members:
	:inherited-members:
	
"""

class DocParser:

	def __init__(self, module, dst):
		# Create our api.rst file
		api_rst = open("api.rst", 'w')
		api_rst.write(API_DOC_HEADER)
	
		# Create api folder
		api_dir = os.path.join(dst, 'api')
		os.makedirs(api_dir, exist_ok=True)
		
		# Now create rst files for the modules
		for i in [getattr(module, i) for i in dir(module) if inspect.ismodule(getattr(module, i))]:
			if not i.__name__.startswith(module.__name__+'.'):
				continue
			name = i.__name__.split('.')[1]
			
			api_rst.write('\tapi/'+name+'\n')
			with open(os.path.join(api_dir, name+'.rst'), 'w') as f:
				f.write(name+'\n')
				f.write('='*len(name)+'\n\n')				
				f.write(AUTODOC_STRING%i.__name__)				
				
		# Close the api.rst file
		api_rst.close()
		
		
if __name__=='__main__':
	sys.path.append('../..')
	import bgui
	doc = DocParser(bgui, '.')