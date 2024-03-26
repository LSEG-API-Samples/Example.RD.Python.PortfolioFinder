#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================

import requests, json
from typing import List
from refinitiv.data.delivery import endpoint_request
from refinitiv.data._errors import ScopeError
from httpx import ReadTimeout

# ----------------------------
# PAM class implements the Portfolio Search API call to retrieve the list of
# portfolios based on the requested parameters.
class PAM():
# ----------------------------
	def __init__(self, controller):
		self.URL = 'https://api.refinitiv.com/user-data/portfolio-management/v1/portfolios/search'
		self.controller = controller

	# Request for the list of portfolios based on the specified request details.
	async def requestPortfolios(self, types: List[str], query: str, maxCount: int):
		params = {}

		params["maximumCount"] = maxCount

		if types is not None:
			params['portfolioTypes'] = ",".join(types)

		if query is not None:
			params["query"] = query
			params["queryField"] = "Any"
			params["queryCondition"] = "Contains"

		# Prepare endpoint definition...
		definition = endpoint_request.Definition(
			url = self.URL,
			query_parameters = params
		)

		# Submit request
		try:
			response = await definition.get_data_async()
			if response.is_success:
				return response.data.raw['portfolioHeaders']
			
			# Throw an exception
			print(f'reason_phrase: {response.raw.reason_phrase}')
			raise RuntimeError(f"Request failed. [Error code: {response.raw.status_code} - {response.raw.reason_phrase}]")
		
		except ReadTimeout as e:
			raise RuntimeError("Request timed out. Consider updating the request timeout within the refinitiv-data.config.json config file")
		
		except ScopeError as e:
			raise RuntimeError(f"Request failed.  Insufficient permissions to access this service: {e.args[0]}")
		
		except RuntimeError:
			raise

		except Exception as e:
			reason = f'Exception: {type(e)}.'
			if len(e.args) > 0:
				reason = f'{reason} {e.args[0]}'
			raise RuntimeError(f"Request failed. {reason}") from None
	

	# Tickhistory REST-GET function
	def _getJsonAsync(self, uri):
		dResp = requests.get(uri, headers=self.hdrs)
		# is it a 202 (in progress)
		while dResp.status_code == 202:
			self.controller.setMsg("waiting for response...")
			# check if the response completed yet
			nURL = dResp.headers['Location']
			dResp = requests.get(nURL, headers=self.hdrs)

		if (dResp.status_code == 200):
			return dResp.json(), ''
		else:
			return None, dResp.json()



	def login(self, username, password):
		pData = {
			"Credentials": {
				"Username": username,
				"Password": password
			}
		}
		dResp = requests.post(f'{self.BASE_URL}/Authentication/RequestToken', data=json.dumps(pData), headers=self.hdrs)

		if (dResp.status_code == 200):
			aToken = dResp.json()['value']
			# keep a copy of the oAuth token for other calls
			self.hdrs["Authorization"] = "Token " + aToken
			return aToken, ''
		else:
			return None, dResp.json()['error']['message']



	def getAllPackages(self):
		uPackages, msg = self._getJsonAsync(f'{self.BASE_URL}/StandardExtractions/UserPackages')
		return uPackages, msg



	def getSchedules(self, packageID):
		delivery, msg = self._getJsonAsync(f'{self.BASE_URL}/StandardExtractions/UserPackageDeliveryGetUserPackageDeliveriesByPackageId(PackageId=\'{packageID}\')')

		# Use Server-Paging to loop through the delivery schedule results and get more previous days
		# while '@odata.nextlink' in delivery:
		# 	self.controller.setMsg("Getting next page...")
		# 	delivery, msg = self._getJsonAsync(delivery['@odata.nextlink'])
		# 	# append the values array in this json message to the root json message

		return delivery, msg



	def downloadFile(self, view, deliveryID, fileName, fileSize, downloadFromAWS=True):
		uri = f'{self.BASE_URL}/StandardExtractions/UserPackageDeliveries(\'{deliveryID}\')/$value'

		downloadHdrs = dict(self.hdrs)
		if downloadFromAWS:
			downloadHdrs['X-Direct-Download'] = 'true'

		dResp = requests.get(uri, headers=downloadHdrs, stream=True)
		# do not auto decompress the data
		dResp.raw.decode_content = False

		chunkSize = 1024*1024
		cStep = chunkSize * 100 / fileSize
		if cStep > 100:
			cStep = 100

		with open(fileName, 'wb') as f:
			step = 1
			for chunk in dResp.iter_content(chunk_size=chunkSize):
				if chunk:
					f.write(chunk)
					progr = int(cStep * step)
					if progr > 100:
						progr = 100

					view.setProgress(progr)
					self.controller.update_idletasks()
					step += 1

		f.close
		self.controller.setMsg(f'File "{fileName}" downloaded')



