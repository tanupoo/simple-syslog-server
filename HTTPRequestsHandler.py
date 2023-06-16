import logging
import requests
from urllib.parse import urlsplit, urlencode
import json

class HTTPRequestsHandler(logging.Handler):
    """
    A class which sends records to a web server using POST.

    the message must be formed specified by ctype.
    this module just sends the message as it is.

    when ctype is application/json (default),
    and if the msg is a dict type. then executes json.dumps(msg).

    logger.debug({"foo":1, "bar":"buzz"})
    the HTTP body becomes { "foo":1, "bar":"buzz" }

    if the msg is like a str type. then makes a dict with a key specified
    by json_default_key, then executes json.dumps().

    logger.debug("foo")
    the HTTP body becomes { "msg": "foo" }

    """
    def __init__(self, url, ctype="application/json",
                 json_default_key="msg",
                 context=None,
                 ):
        """
        Initialize the instance.

        url: unlike original HTTPHandler, url must contain everything
            such as "http://example.com/log".
            the credentials can be contained with the manner of requests
            module.  if the scheme of the url is https, context must be
            defined.
        ctype: content-type.  default is "application/json"
        json_default_key: the default key for JSON.  it's valid when ctype
            is "application/json".
        """
        logging.Handler.__init__(self)
        p = urlsplit(url)
        if p.scheme == "https" and context is None:
            raise ValueError("context parameter must be defined for https.")
        self.url = url
        self.ctype = ctype
        self.context = context
        self.json_default_key = json_default_key
        if self.ctype == "application/json":
            self.__json = True
        else:
            self.__json = False

    def emit(self, record):
        """
        Emit a record.

        Send the record to the web server as a percent-encoded dictionary
        """
        # set headers
        headers = { "content-type": self.ctype }
        msg = record.msg
        if self.__json:
            if isinstance(msg, dict):
                body = json.dumps(msg)
            else:
                body = json.dumps({ self.json_default_key: msg })
        else:
            body = urlencode(str(msg))
        # submitting.
        print(body)
        try:
            ret = requests.post(self.url, headers=headers, data=body)
        except Exception as e:
            print("ERROR:", e)
            return False
        else:
            if ret.ok:
                return True
            else:
                print("ERROR:", ret.status_code)
                return False

