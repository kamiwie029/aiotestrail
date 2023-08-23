"""Async TestRail API binding for Python 3.x.

http://docs.gurock.com/testrail-api2/start
http://docs.gurock.com/testrail-api2/accessing
"""

import base64
import json
import aiohttp 
import requests

class APIClient:
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'
    
    async def send_get_async(self, uri, session: aiohttp.ClientSession, filepath=None) -> dict:
        """Issue an asynchronous GET request (read) against the API.

        You can find all the API endpoints on the testrai's API Reference page.


        Arguments
        ------------
        uri: `str`
            The API method to call including parameters, e.g. get_case/1.
        session: `aiohttp.ClientSession` 
            The session to use to send requests.
        filepath: Optional[`str`]
            The path and file name for attachment download; 
            used only for 'get_attachment/:attachment_id'.

        Returns:
        ------------
            A dict containing the result of the request.
        """
        return await self.__send_async_request('GET', uri, session, filepath)

    async def send_post_async(self, uri, session:  aiohttp.ClientSession, data) -> dict:
        """Issue an asynchronous POST request (write) against the API.

        You can find all the API endpoints on the testrai's API Reference page.

        Arguments
        ------------
        uri: `str`
            The API method to call, including parameters, e.g. add_case/1.
        session: `aiohttp.ClientSession` 
            The session to use to send requests.
        data: `dict|str`
            The data to submit as part of the request as a dict; strings
            must be UTF-8 encoded. If adding an attachment, must be the
            path to the file.

        Returns:
        ------------
            A dict containing the result of the request.
        """
        return await self.__send_async_request('POST', uri, session, data)

    async def __handle_errors(self, response):
        if response.status > 201:
            try:
                error = await response.json()
            except:     # response.content not formatted as JSON
                error = str(response.content)
            raise APIError('TestRail API returned HTTP %s (%s)' % (response.status, error))
   
    async def __return_response(self, response):
        try:
            return await response.json()
        except: # Nothing to return
            return {}

    async def __send_async_request(self, method,  path: str, session: aiohttp.ClientSession, data=None):
        auth = str(base64.b64encode(bytes(f'{self.user}:{self.password}', 'utf-8')),'ascii').strip()
        headers = {'Authorization': 'Basic ' + auth}
        uri = self.__url + path

        if method == "POST":
            assert data, f"There's no data to post, got: data = {data}"
       
            return await self.__send_async_post(uri, session=session, headers=headers)
       
        else:
            attachment = data if uri.startswith('get_attachment/') else None
            return await self.__send_async_get(uri, session=session, headers=headers, attachment=attachment)

    async def __send_async_post(self, uri, data, session: aiohttp.ClientSession, headers):
        async def __post(session, uri, **kwargs):
            async with session.post(uri, **kwargs) as response:
                await self.__handle_errors(response)

                return await self.__return_response(response)
               

        if uri.startswith('add_attachment'):    # add_attachment API method
            files = {'attachment': (open(data, 'rb'))}
            result = await __post(session, uri, files=files)
            files['attachment'].close()
            return result
        else:
            headers['Content-Type'] = 'application/json'
            payload = bytes(json.dumps(data), 'utf-8')
            return await __post(session, uri, data=payload)
   
    async def __send_async_get(self, url: str, session: aiohttp.ClientSession, attachment=None, **kwargs):
        async with session.get(url, **kwargs) as response:
            await self.__handle_errors(response)

            if attachment:
                try:
                    open(attachment, 'wb').write(response.content)
                    return (attachment)
                except:
                    return ("Error saving attachment.")
       
            return await self.__return_response(response)

    def send_get(self, uri, filepath=None):
        """Issue a synchronous (default) GET request (read) against the API.

        Args:
            uri: The API method to call including parameters, e.g. get_case/1.
            filepath: The path and file name for attachment download; used only
                for 'get_attachment/:attachment_id'.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('GET', uri, filepath)

    def send_post(self, uri, data):
        """Issue a synchronous (default) POST request (write) against the API.

        Args:
            uri: The API method to call, including parameters, e.g. add_case/1.
            data: The data to submit as part of the request as a dict; strings
                must be UTF-8 encoded. If adding an attachment, must be the
                path to the file.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri

        auth = str(
            base64.b64encode(
                bytes('%s:%s' % (self.user, self.password), 'utf-8')
            ),
            'ascii'
        ).strip()
        headers = {'Authorization': 'Basic ' + auth}

        if method == 'POST':
            if uri[:14] == 'add_attachment':    # add_attachment API method
                files = {'attachment': (open(data, 'rb'))}
                response = requests.post(url, headers=headers, files=files)
                files['attachment'].close()
            else:
                headers['Content-Type'] = 'application/json'
                payload = bytes(json.dumps(data), 'utf-8')
                response = requests.post(url, headers=headers, data=payload)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)

        if response.status_code > 201:
            try:
                error = response.json()
            except:     # response.content not formatted as JSON
                error = str(response.content)
            raise APIError('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
        else:
            if uri[:15] == 'get_attachment/':   # Expecting file, not JSON
                try:
                    open(data, 'wb').write(response.content)
                    return (data)
                except:
                    return ("Error saving attachment.")
            else:
                try:
                    return response.json()
                except: # Nothing to return
                    return {}

class APIError(Exception):
    pass
