import json
import logging
from base64 import b64encode
from io import BytesIO
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


class FrappeException(Exception):
    pass


class NotUploadableException(FrappeException):
    def __init__(self, doctype):
        self.message = f"The doctype `{doctype}` is not uploadable, so you can't download the template"


class AsyncFrappeClient(object):
    def __init__(self, url: str, api_key: str, api_secret: str, verify: bool = True):
        self.headers = dict(Accept="application/json")
        self.can_download = []
        self.url = url
        self.session = httpx.AsyncClient(verify=verify, headers=self.headers, follow_redirects=True, timeout=20)

        try:
            self.authenticate(api_key, api_secret)
        except Exception:
            logger.error("Authentication failed", exc_info=True)
            raise

    def __enter__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.logout()

    def authenticate(self, api_key, api_secret):
        token = b64encode(f"{api_key}:{api_secret}".encode()).decode()
        auth_header = {"Authorization": f"Basic {token}"}
        self.session.headers.update(auth_header)

    async def logout(self):
        await self.session.get(
            self.url,
            params={
                "cmd": "logout",
            },
        )

    async def get_list(
        self,
        doctype,
        fields=None,
        filters=None,
        limit_start=0,
        limit_page_length=0,
        order_by=None,
        or_filters=None,
    ):
        """Returns list of records of a particular type"""
        fields = fields or ["*"]

        if not isinstance(fields, str):
            fields = json.dumps(fields)

        params = {
            "fields": fields,
        }
        if filters:
            params["filters"] = json.dumps(filters, default=str)
        if or_filters:
            params["or_filters"] = json.dumps(or_filters, default=str)
        if limit_page_length:
            params["limit_start"] = limit_start
            params["limit_page_length"] = limit_page_length
        if order_by:
            params["order_by"] = order_by

        res = await self.session.get(self.url + "/api/resource/" + doctype, params=params)
        return self.post_process(res)

    async def insert(self, doc):
        """Insert a document to the remote server

        :param doc: A dict or Document object to be inserted remotely"""
        res = await self.session.post(
            self.url + "/api/resource/" + quote(doc.get("doctype")),
            data={"data": json.dumps(doc, default=str)},
        )
        return self.post_process(res)

    async def insert_many(self, docs):
        """Insert multiple documents to the remote server

        :param docs: List of dict or Document objects to be inserted in one request"""
        return await self.post_request({"cmd": "frappe.client.insert_many", "docs": json.dumps(docs, default=str)})

    async def update(self, doc):
        """Update a remote document

        :param doc: dict or Document object to be updated remotely. `name` is mandatory for this"""
        url = self.url + "/api/resource/" + quote(doc.get("doctype")) + "/" + quote(doc.get("name"))
        res = await self.session.put(url, data={"data": json.dumps(doc, default=str)})
        return self.post_process(res)

    async def bulk_update(self, docs):
        """Bulk update documents remotely

        :param docs: List of dict or Document objects to be updated remotely (by `name`)"""
        return await self.post_request({"cmd": "frappe.client.bulk_update", "docs": json.dumps(docs, default=str)})

    async def delete(self, doctype, name):
        """Delete remote document by name

        :param doctype: `doctype` to be deleted
        :param name: `name` of document to be deleted"""
        return await self.post_request({"cmd": "frappe.client.delete", "doctype": doctype, "name": name})

    async def submit(self, doc: dict):
        """Submit remote document

        :param doc: dict or Document object to be submitted remotely"""
        return await self.post_request({"cmd": "frappe.client.submit", "doclist": json.dumps(doc)})

    async def get_value(self, doctype, fieldname=None, filters=None):
        return await self.get_request(
            {
                "cmd": "frappe.client.get_value",
                "doctype": doctype,
                "fieldname": fieldname or "name",
                "filters": json.dumps(filters),
            }
        )

    async def set_value(self, doctype, docname, fieldname, value):
        return await self.post_request(
            {
                "cmd": "frappe.client.set_value",
                "doctype": doctype,
                "name": docname,
                "fieldname": fieldname,
                "value": value,
            }
        )

    async def cancel(self, doctype, name):
        return await self.post_request({"cmd": "frappe.client.cancel", "doctype": doctype, "name": name})

    async def get_doc(self, doctype, name="", filters=None, fields=None):
        """Returns a single remote document

        :param doctype: DocType of the document to be returned
        :param name: (optional) `name` of the document to be returned
        :param filters: (optional) Filter by this dict if name is not set
        :param fields: (optional) Fields to be returned, will return everythign if not set"""
        params = {}
        if filters:
            params["filters"] = json.dumps(filters)
        if fields:
            params["fields"] = json.dumps(fields)

        res = await self.session.get(self.url + "/api/resource/" + doctype + "/" + name, params=params)

        return self.post_process(res)

    async def rename_doc(self, doctype, old_name, new_name):
        """Rename remote document

        :param doctype: DocType of the document to be renamed
        :param old_name: Current `name` of the document to be renamed
        :param new_name: New `name` to be set"""
        params = {"cmd": "frappe.client.rename_doc", "doctype": doctype, "old_name": old_name, "new_name": new_name}
        return self.post_request(params)

    async def get_pdf(self, doctype, name, print_format="Standard", letterhead=True):
        params = {"doctype": doctype, "name": name, "format": print_format, "no_letterhead": int(not bool(letterhead))}

        async with self.session.stream(
            "GET",
            self.url + "/api/method/frappe.templates.pages.print.download_pdf",
            params=params,
        ) as response:
            return await self.post_process_file_stream(response)

    async def get_html(self, doctype, name, print_format="Standard", letterhead=True):
        params = {"doctype": doctype, "name": name, "format": print_format, "no_letterhead": int(not bool(letterhead))}
        async with self.session.stream(
            "GET",
            self.url + "/print",
            params=params,
        ) as response:
            return await self.post_process_file_stream(response)

    async def __load_downloadable_templates(self):
        self.can_download = await self.get_api("frappe.core.page.data_import_tool.data_import_tool.get_doctypes")

    async def get_upload_template(self, doctype, with_data=False):
        if not self.can_download:
            await self.__load_downloadable_templates()

        if doctype not in self.can_download:
            raise NotUploadableException(doctype)

        params = {
            "doctype": doctype,
            "parent_doctype": doctype,
            "with_data": "Yes" if with_data else "No",
            "all_doctypes": "Yes",
        }

        async with self.session.stream(
            "GET",
            self.url + "/api/method/frappe.core.page.data_import_tool.exporter.get_template",
            params=params,
        ) as response:
            return self.post_process_file_stream(response)

    async def get_api(self, method, params: dict | None = None):
        params = params or {}
        res = await self.session.get(self.url + "/api/method/" + method + "/", params=params)
        return self.post_process(res)

    async def post_api(self, method, params: dict | None = None):
        params = params or {}
        res = await self.session.post(self.url + "/api/method/" + method + "/", params=params)
        return self.post_process(res)

    async def get_request(self, params):
        res = await self.session.get(self.url, params=self.preprocess(params))
        res = self.post_process(res)
        return res

    async def post_request(self, data):
        res = await self.session.post(self.url, data=self.preprocess(data))
        res = self.post_process(res)
        return res

    @staticmethod
    def preprocess(params):
        """convert dicts, lists to json"""
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                params[key] = json.dumps(value)

        return params

    @staticmethod
    def post_process(response):
        try:
            rjson = response.json()
        except ValueError:
            logger.error(response.text)
            raise

        if rjson and ("exc" in rjson) and rjson["exc"]:
            raise FrappeException(rjson["exc"])
        if "message" in rjson:
            return rjson["message"]
        elif "data" in rjson:
            return rjson["data"]
        else:
            return None

    @staticmethod
    async def post_process_file_stream(response: httpx.Response):
        if response.status_code == 200:
            output = BytesIO()
            async for block in response.aiter_bytes(chunk_size=1024):
                output.write(block)
            return output
        else:
            try:
                rjson = await response.json()
            except ValueError:
                logger.error(await response.aread())
                raise

            if rjson and ("exc" in rjson) and rjson["exc"]:
                raise FrappeException(rjson["exc"])
            if "message" in rjson:
                return rjson["message"]
            elif "data" in rjson:
                return rjson["data"]
            else:
                return None
