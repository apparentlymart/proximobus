
from proximobus import service, handlers

def main():
    request = service.Request.from_cgi_environment()
    response = handlers.handle_request(request)
    print "Content-type: "+str(response.content_type)
    print "Access-Control-Allow-Origin: *"
    print
    print response.content


#try:
main()
#except service.HTTPError as err:
#    print "Status: "+str(err.status)+" Bad"
#    print "Content-type: text/html"
#    print
#    print "Error "+str(err.status)+": "+err.message


