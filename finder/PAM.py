#=============================================================================
#   This source code is provided under the Apache 2.0 license
#   and is provided AS IS with no warranty or guarantee of fit for purpose.
#   Copyright (C) 2024 LSEG. All rights reserved.
#=============================================================================

from typing import List
from refinitiv.data.delivery import endpoint_request
from refinitiv.data._errors import ScopeError
from httpx import ReadTimeout
import asyncio
import pandas as pd

# ----------------------------
# PAM class implements the Portfolio Search API call to retrieve the list of
# portfolios based on the requested parameters.
class PAM():
# ----------------------------
	def __init__(self, controller):
		self.URL = 'https://api.refinitiv.com/user-data/portfolio-management/v1/portfolios/search'
		self.controller = controller
		self.definition = None

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
		if self.definition is None:
			# Note: The 1st endpoint definition request will block and load modules thus we wrap an async/await
			self.definition = await asyncio.get_event_loop().run_in_executor(None, endpoint_request.Definition, self.URL)
		
		self.definition.query_parameters = params

		# Submit request
		try:
			response = await self.definition.get_data_async()
			if response.is_success:
				return pd.DataFrame(response.data.raw['portfolioHeaders'])
			
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
