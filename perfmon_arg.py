#!/usr/bin/python3
"""Serviceability Perfmon <perfmonCollectCounterData> sample script

Performs a <perfmonCollectCounterData> request for the 'Cisco CallManager' object
using the Zeep SOAP library, and parses/prints the results in a simple table output.

Dependency Installation:

	$ pip3 install -r requirements.txt

Copyright (c) 2018 Cisco and/or its affiliates.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault
import urllib3
import datetime
from influxdb import InfluxDBClient
import argparse
parser = argparse.ArgumentParser()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Change to true to enable output of request/response headers and XML
DEBUG = False

# The WSDL is a local file in the working directory, see README
WSDL_FILE = '/opt/nested/scripts/schema/PerfmonService.wsdl'

# This class lets you view the incoming and outgoing HTTP headers and XML

class MyLoggingPlugin( Plugin ):

	def egress( self, envelope, http_headers, operation, binding_options ):

		# Format the request body as pretty printed XML
		xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')

		print( f'\nRequest\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )

	def ingress( self, envelope, http_headers, operation ):

		# Format the response body as pretty printed XML
		xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')

		print( f'\nResponse\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )

# main function
def main(CUCM_ADDRESSES,USERNAME,PASSWORD,COUNTER_OBJECT):
	
	for server in CUCM_ADDRESSES:
	
		# The first step is to create a SOAP client session

		session = Session()
		session.trust_env = False

		# We disable certificate verification by default

		session.verify = False

		# To enabled SSL cert checking (recommended for production)
		# place the CUCM Tomcat cert .pem file in the root of the project
		# and uncomment the two lines below

		# CERT = 'changeme.pem'
		# session.verify = CERT

		session.auth = HTTPBasicAuth( USERNAME, PASSWORD )

		transport = Transport( session = session, timeout = 10 )

		# strict=False is not always necessary, but it allows zeep to parse imperfect XML
		settings = Settings( strict = False, xml_huge_tree = True )

		# If debug output is requested, add the MyLoggingPlugin class
		plugin = [ MyLoggingPlugin() ] if DEBUG else [ ]

		# Create the Zeep client with the specified settings
		client = Client( WSDL_FILE, settings = settings, transport = transport, plugins = plugin )

		# Create the Zeep service binding to the Perfmon SOAP service at the specified CUCM
		service = client.create_service(
			'{http://schemas.cisco.com/ast/soap}PerfmonBinding',
			f'https://{server}:8443/perfmonservice2/services/PerfmonService' 
			)
			

		# Execute the request
		try:
			resp = service.perfmonCollectCounterData(
				Host = server,
				Object = COUNTER_OBJECT
				)
		except Fault as err:
			print( f'Zeep error: perfmonCollectCounterData: {err}' )
		else:
			if DEBUG == True:
				print( "\nperfmonCollectCounterData response:\n" )
				print( resp,"\n" )
		
		if DEBUG == True:
			input( 'Press Enter to continue...' )

			# Create a simple report of the XML response
			print( '\nperfmonCollectCounterData output for "'+ COUNTER_OBJECT + '"' )
			print( '=======================================================\n')

		# Loop through the top-level of the response object
		for item in resp:

			# Extract the final value in the counter path, which sould be the counter name
			counterPath = item.Name._value_1
			counterArr = list(filter(None, counterPath.split('\\')))
			last = counterPath.rfind( '\\' ) + 1
			counterName = counterPath[ last: ]
			
			if DEBUG == True:
				# Print the name and value, padding/truncating the name to 20 characters
				print( '{:20}{:20}{:20}'.format(counterArr[0],counterArr[1],counterArr[2] ) + ' : ' + str( item.Value ) )
			
			json_body = [
				{
					"measurement": COUNTER_OBJECT.lower().replace(" ","_"),
					"tags":{
						"server": counterArr[0],
						"counter": counterArr[1],
						"instance": counterArr[2],  
					},
					"fields": {
						"value": item.Value
					}
				}
			]

			
			client = InfluxDBClient('170.2.96.200', 8086, '', '', 'rtmt')
			client.write_points(json_body)
			
			if DEBUG == True:
				result = client.query("select LAST(*) from " + json_body[0]['measurement'])
				print ("Succesfully recorded result: {0}".format(result))


if __name__ == '__main__':    
	parser.add_argument( "-ip","--hostname", required=True, nargs="+", type=str, help="Hostname/IP separated by space" )    
	parser.add_argument("-u", "--username", required=True, help="User name")
	parser.add_argument("-p", "--password", required=True, help="Password")
	parser.add_argument("-c", "--counter", help="Counter", default="Cisco CallManager")

	args = parser.parse_args()
	
	main(args.hostname,args.username,args.password,args.counter)