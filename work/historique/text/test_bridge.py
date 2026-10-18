import copy,json,unittest
from bridge import PROTOCOL,validate_request,validate_result,encode_request,decode_result,french_response

class BridgeTests(unittest.TestCase):
    def request(self):
        return {'protocol':PROTOCOL,'id':'request_001','type':'request','status':'ready','task':'calculate','goal':'Compute total price from quantity and unit_price.','data':{'quantity':3,'unit_price':2.5,'unit':'eur'},'constraints':[{'key':'unit','op':'eq','value':'eur'}],'context':{},'missing':[]}

    def result(self):
        return {'protocol':PROTOCOL,'id':'request_001','type':'result','status':'ok','answer':'The total is 7.5 EUR.','values':{'total':7.5,'unit':'eur','available':True,'discount':None},'missing':[]}

    def test_transport_and_french_rendering_preserve_typed_values(self):
        request=self.request();self.assertEqual(json.loads(encode_request(request)),request)
        result=decode_result(json.dumps(self.result()),request)
        french=french_response(result,'Le total est de 7,50 €.',request)
        self.assertEqual(french['valeurs'],self.result()['values'])
        self.assertIs(type(french['valeurs']['total']),float)
        self.assertIs(type(french['valeurs']['available']),bool)
        self.assertIsNone(french['valeurs']['discount'])
        french['valeurs']['total']=99
        self.assertEqual(result['values']['total'],7.5)

    def test_unknown_information_stays_explicit_and_is_not_dispatched(self):
        request=self.request();request.update(status='clarify',missing=['unit_price']);request['data']['unit_price']=None
        validate_request(request)
        with self.assertRaises(ValueError):encode_request(request)
        with self.assertRaises(ValueError):validate_result(self.result(),request)
        request['status']='ready'
        with self.assertRaises(ValueError):validate_request(request)

    def test_rejects_mismatched_ids_versions_fields_and_nonfinite_numbers(self):
        for field,value in [('id','other_request'),('protocol','input.bridge/9'),('values',{'total':float('nan')}),('extra','unexpected')]:
            result=self.result();result[field]=value
            with self.assertRaises(ValueError):validate_result(result,self.request())
        with self.assertRaises(ValueError):decode_result('{"id":"a","id":"b"}',self.request())

    def test_constraints_unknown_codes_and_keys_are_not_silently_rewritten(self):
        for change in ({'task':'execute_shell'},{'data':{'Prix Unitaire':2.5}},{'constraints':[{'key':'total','op':'in','value':4}]},{'missing':['unit_price','unit_price']}):
            request=self.request();request.update(change)
            with self.assertRaises(ValueError):validate_request(request)

if __name__=='__main__':unittest.main()
